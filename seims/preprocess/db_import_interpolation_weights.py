#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate weight data for interpolate of hydroclimate data
    @author   : Liangjun Zhu, Junzhi Liu
    @changelog: 16-12-07  lj - rewrite for version 2.0
                17-06-26  lj - reorganize according to pylint and google style
"""
from math import sqrt, pow
from struct import pack, unpack

from numpy import zeros as np_zeros
from gridfs import GridFS

from seims.preprocess.db_mongodb import MongoQuery
from seims.preprocess.text import DBTableNames, RasterMetadata, FieldNames, \
    DataType, StationFields, DataValueFields
from seims.preprocess.utility import UTIL_ZERO


class ImportWeightData(object):
    """Spatial weight and its related data"""

    @staticmethod
    def cal_dis(x1, y1, x2, y2):
        """calculate distance between two points"""
        dx = x2 - x1
        dy = y2 - y1
        return sqrt(dx * dx + dy * dy)

    @staticmethod
    def idw(x, y, loc_list):
        """IDW method for weight
        This function is not used currently"""
        ex = 2
        coef_list = []
        sum_dist = 0
        for pt in loc_list:
            dis = ImportWeightData.cal_dis(x, y, pt[0], pt[1])
            coef = pow(dis, -ex)
            coef_list.append(coef)
            sum_dist += coef
        weight_list = []
        for coef in coef_list:
            weight_list.append(coef / sum_dist)
        # print weight_list
        fmt = '%df' % (len(weight_list))
        s = pack(fmt, *weight_list)
        return s

    @staticmethod
    def thiessen(x, y, loc_list):
        """Thiessen polygon method for weights"""
        i_min = 0
        coef_list = []
        # print loc_list
        if len(loc_list) <= 1:
            coef_list.append(1)
            fmt = '%df' % 1
            return pack(fmt, *coef_list), i_min

        dis_min = ImportWeightData.cal_dis(x, y, loc_list[0][0], loc_list[0][1])

        coef_list.append(0)

        for i in range(1, len(loc_list)):
            coef_list.append(0)
            dis = ImportWeightData.cal_dis(x, y, loc_list[i][0], loc_list[i][1])
            # print x, y, loc_list[i][0], loc_list[i][1], dis
            if dis < dis_min:
                i_min = i
                dis_min = dis
        coef_list[i_min] = 1
        fmt = '%df' % (len(coef_list))

        s = pack(fmt, *coef_list)
        return s, i_min

    @staticmethod
    def generate_weight_dependent_parameters(conn, maindb, subbsn_id):
        """Generate some parameters dependent on weight data and only should be calculated once.
            Such as PHU0 (annual average total potential heat units)
                TMEAN0 (annual average temperature)
            added by Liangjun, 2016-6-17
        """
        spatial_gfs = GridFS(maindb, DBTableNames.gridfs_spatial)
        # read mask file from mongodb
        mask_name = str(subbsn_id) + '_MASK'
        # is MASK existed in Database?
        if not spatial_gfs.exists(filename=mask_name):
            raise RuntimeError('%s is not existed in MongoDB!' % mask_name)
        # read WEIGHT_M file from mongodb
        weight_m_name = str(subbsn_id) + '_WEIGHT_M'
        mask = maindb[DBTableNames.gridfs_spatial].files.find({"filename": mask_name})[0]
        weight_m = maindb[DBTableNames.gridfs_spatial].files.find({"filename": weight_m_name})[0]
        num_cells = int(weight_m["metadata"][RasterMetadata.cellnum])
        num_sites = int(weight_m["metadata"][RasterMetadata.site_num])
        # read meteorology sites
        site_lists = maindb[DBTableNames.main_sitelist].find({FieldNames.subbasin_id: subbsn_id})
        site_list = site_lists.next()
        db_name = site_list[FieldNames.db]
        m_list = site_list.get(FieldNames.site_m)
        hydro_clim_db = conn[db_name]

        site_list = m_list.split(',')
        site_list = [int(item) for item in site_list]

        q_dic = {StationFields.id: {'$in': site_list},
                 StationFields.type: DataType.phu0}
        cursor = hydro_clim_db[DBTableNames.annual_stats].find(q_dic).sort(StationFields.id, 1)

        q_dic2 = {StationFields.id: {'$in': site_list},
                  StationFields.type: DataType.mean_tmp0}
        cursor2 = hydro_clim_db[DBTableNames.annual_stats].find(q_dic2).sort(StationFields.id, 1)

        id_list = []
        phu_list = []
        for site in cursor:
            id_list.append(site[StationFields.id])
            phu_list.append(site[DataValueFields.value])

        id_list2 = []
        tmean_list = []
        for site in cursor2:
            id_list2.append(site[StationFields.id])
            tmean_list.append(site[DataValueFields.value])

        weight_m_data = spatial_gfs.get(weight_m["_id"])
        total_len = num_cells * num_sites
        # print (total_len)
        fmt = '%df' % (total_len,)
        weight_m_data = unpack(fmt, weight_m_data.read())

        # calculate PHU0
        phu0_data = np_zeros(num_cells)
        # calculate TMEAN0
        tmean0_data = np_zeros(num_cells)
        for i in range(num_cells):
            for j in range(num_sites):
                phu0_data[i] += phu_list[j] * weight_m_data[i * num_sites + j]
                tmean0_data[i] += tmean_list[j] * weight_m_data[i * num_sites + j]
        ysize = int(mask["metadata"][RasterMetadata.nrows])
        xsize = int(mask["metadata"][RasterMetadata.ncols])
        nodata_value = mask["metadata"][RasterMetadata.nodata]
        mask_data = spatial_gfs.get(mask["_id"])
        total_len = xsize * ysize
        fmt = '%df' % (total_len,)
        mask_data = unpack(fmt, mask_data.read())
        fname = "%s_%s" % (str(subbsn_id), DataType.phu0)
        fname2 = "%s_%s" % (str(subbsn_id), DataType.mean_tmp0)
        if spatial_gfs.exists(filename=fname):
            x = spatial_gfs.get_version(filename=fname)
            spatial_gfs.delete(x._id)
        if spatial_gfs.exists(filename=fname2):
            x = spatial_gfs.get_version(filename=fname2)
            spatial_gfs.delete(x._id)
        meta_dic = mask["metadata"]
        meta_dic["TYPE"] = DataType.phu0
        meta_dic["ID"] = fname
        meta_dic["DESCRIPTION"] = DataType.phu0

        meta_dic2 = mask["metadata"]
        meta_dic2["TYPE"] = DataType.mean_tmp0
        meta_dic2["ID"] = fname2
        meta_dic2["DESCRIPTION"] = DataType.mean_tmp0

        myfile = spatial_gfs.new_file(filename=fname, metadata=meta_dic)
        myfile2 = spatial_gfs.new_file(filename=fname2, metadata=meta_dic2)
        vaild_count = 0
        for i in range(0, ysize):
            cur_row = []
            cur_row2 = []
            for j in range(0, xsize):
                index = i * xsize + j
                # print index
                if abs(mask_data[index] - nodata_value) > UTIL_ZERO:
                    cur_row.append(phu0_data[vaild_count])
                    cur_row2.append(tmean0_data[vaild_count])
                    vaild_count += 1
                else:
                    cur_row.append(nodata_value)
                    cur_row2.append(nodata_value)
            fmt = '%df' % xsize
            myfile.write(pack(fmt, *cur_row))
            myfile2.write(pack(fmt, *cur_row2))
        myfile.close()
        myfile2.close()
        print ("Valid Cell Number is: %d" % vaild_count)
        return True

    @staticmethod
    def climate_itp_weight_thiessen(conn, db_model, subbsn_id, storm_mode, geodata2dbdir):
        """Generate and import weight information using Thiessen polygon method.

        Args:
            conn:
            db_model: workflow database object
            subbsn_id: subbasin id
            storm_mode: is storm mode or not
            geodata2dbdir: directory to store weight data as txt file
        """
        spatial_gfs = GridFS(db_model, DBTableNames.gridfs_spatial)
        # read mask file from mongodb
        mask_name = str(subbsn_id) + '_MASK'
        if not spatial_gfs.exists(filename=mask_name):
            raise RuntimeError('%s is not existed in MongoDB!' % mask_name)
        mask = db_model[DBTableNames.gridfs_spatial].files.find({"filename": mask_name})[0]
        ysize = int(mask["metadata"][RasterMetadata.nrows])
        xsize = int(mask["metadata"][RasterMetadata.ncols])
        nodata_value = mask["metadata"][RasterMetadata.nodata]
        dx = mask["metadata"][RasterMetadata.cellsize]
        xll = mask["metadata"][RasterMetadata.xll]
        yll = mask["metadata"][RasterMetadata.yll]

        data = spatial_gfs.get(mask["_id"])

        total_len = xsize * ysize
        fmt = '%df' % (total_len,)
        data = unpack(fmt, data.read())
        # print data[0], len(data), type(data)

        # count number of valid cells
        num = 0
        for type_i in range(0, total_len):
            if abs(data[type_i] - nodata_value) > UTIL_ZERO:
                num += 1

        # read stations information from database
        metadic = {RasterMetadata.subbasin: subbsn_id,
                   RasterMetadata.cellnum: num}
        site_lists = db_model[DBTableNames.main_sitelist].find({FieldNames.subbasin_id: subbsn_id})
        site_list = site_lists.next()
        clim_db_name = site_list[FieldNames.db]
        p_list = site_list.get(FieldNames.site_p)
        m_list = site_list.get(FieldNames.site_m)
        pet_list = site_list.get(FieldNames.site_pet)
        # print p_list
        # print m_list
        hydro_clim_db = conn[clim_db_name]

        type_list = [DataType.m, DataType.p, DataType.pet]
        site_lists = [m_list, p_list, pet_list]
        if pet_list is None:
            del type_list[2]
            del site_lists[2]

        if storm_mode:
            type_list = [DataType.p]
            site_lists = [p_list]
            # print type_list
        # print site_lists

        for type_i, type_name in enumerate(type_list):
            fname = '%d_WEIGHT_%s' % (subbsn_id, type_name)
            print fname
            if spatial_gfs.exists(filename=fname):
                x = spatial_gfs.get_version(filename=fname)
                spatial_gfs.delete(x._id)
            site_list = site_lists[type_i]
            if site_list is not None:
                site_list = site_list.split(',')
                # print site_list
                site_list = [int(item) for item in site_list]
                metadic[RasterMetadata.site_num] = len(site_list)
                # print site_list
                q_dic = {StationFields.id: {'$in': site_list},
                         StationFields.type: type_list[type_i]}
                cursor = hydro_clim_db[DBTableNames.sites].find(q_dic).sort(StationFields.id, 1)

                # meteorology station can also be used as precipitation station
                if cursor.count() == 0 and type_list[type_i] == DataType.p:
                    q_dic = {StationFields.id.upper(): {'$in': site_list},
                             StationFields.type.upper(): DataType.m}
                    cursor = hydro_clim_db[DBTableNames.sites].find(q_dic). \
                        sort(StationFields.id, 1)

                # get site locations
                id_list = []
                loc_list = []
                for site in cursor:
                    if site[StationFields.id] in site_list:
                        id_list.append(site[StationFields.id])
                        loc_list.append([site[StationFields.x], site[StationFields.y]])
                # print 'loclist', locList
                # interpolate using the locations
                # weightList = []
                myfile = spatial_gfs.new_file(filename=fname, metadata=metadic)
                f_test = open(r"%s/weight_%d_%s.txt" % (geodata2dbdir,
                                                        subbsn_id, type_list[type_i]), 'w')
                for y in range(0, ysize):
                    for x in range(0, xsize):
                        index = int(y * xsize + x)
                        # print index
                        if abs(data[index] - nodata_value) > UTIL_ZERO:
                            x_coor = xll + x * dx
                            y_coor = yll + (ysize - y - 1) * dx
                            near_index = 0
                            # print locList
                            line, near_index = ImportWeightData.thiessen(x_coor, y_coor, loc_list)
                            myfile.write(line)
                            fmt = '%df' % (len(loc_list))
                            f_test.write("%f %f " % (x, y) + unpack(fmt, line).__str__() + "\n")
                myfile.close()
                f_test.close()

    @staticmethod
    def workflow(cfg, conn):
        """Workflow"""
        db_model = conn[cfg.spatial_db]
        subbasin_start_id = 0
        n_subbasins = 0  # default is for OpenMP version
        if cfg.cluster:
            subbasin_start_id = 1
            n_subbasins = MongoQuery.get_subbasin_num(db_model)

        for subbsn_id in range(subbasin_start_id, n_subbasins + 1):
            ImportWeightData.climate_itp_weight_thiessen(conn, db_model, subbsn_id,
                                                         cfg.storm_mode, cfg.dirs.geodata2db)
            ImportWeightData.generate_weight_dependent_parameters(conn, db_model, subbsn_id)


def main():
    """TEST CODE"""
    from seims.preprocess.config import parse_ini_configuration
    from seims.preprocess.db_mongodb import ConnectMongoDB
    seims_cfg = parse_ini_configuration()
    client = ConnectMongoDB(seims_cfg.hostname, seims_cfg.port)
    conn = client.get_conn()

    ImportWeightData.workflow(seims_cfg, conn)

    client.close()


if __name__ == "__main__":
    main()
