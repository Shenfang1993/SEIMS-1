#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Import BMP Scenario related parameters to MongoDB
    @author   : Liangjun Zhu
    @changelog: 16-06-16  first implementation version
                17-06-22  improve according to pylint and google style
"""
from os import sep as SEP

from seims.preprocess.text import DBTableNames
from seims.preprocess.utility import read_data_items_from_txt
from seims.pygeoc.pygeoc.raster.raster import RasterUtilClass
from seims.pygeoc.pygeoc.utils.utils import MathClass, FileClass, StringClass


class ImportScenario2Mongo(object):
    """Import scenario data to MongoDB
    """
    _FLD_DB = 'DB'
    _LocalX = 'LocalX'
    _LocalY = 'LocalY'
    _DISTDOWN = "DIST2REACH"
    _SUBBASINID = "SUBBASINID"

    @staticmethod
    def scenario_from_texts(cfg, main_db, scenario_db):
        """Import BMPs Scenario data to MongoDB
        Args:
            cfg: SEIMS configuration object
            main_db: climate database
            scenario_db: scenario database
        Returns:
            False if failed, otherwise True.
        """
        if not cfg.use_scernario:
            return False
        print ("Import BMP Scenario Data... ")
        bmp_files = FileClass.get_filename_by_suffixes(cfg.scenario_dir, ['.txt'])
        bmp_tabs = []
        bmp_tabs_path = []
        for f in bmp_files:
            bmp_tabs.append(f.split('.')[0])
            bmp_tabs_path.append(cfg.scenario_dir + SEP + f)

        # create if collection not existed
        c_list = scenario_db.collection_names()
        for item in bmp_tabs:
            if not StringClass.string_in_list(item.upper(), c_list):
                scenario_db.create_collection(item.upper())
            else:
                scenario_db.drop_collection(item.upper())
        # Read subbasin.tif and dist2Stream.tif
        subbasin_r = RasterUtilClass.read_raster(cfg.spatials.subbsn)
        dist2stream_r = RasterUtilClass.read_raster(cfg.spatials.dist2stream_d8)
        # End reading
        for j, bmp_txt in enumerate(bmp_tabs_path):
            bmp_tab_name = bmp_tabs[j]
            data_array = read_data_items_from_txt(bmp_txt)
            field_array = data_array[0]
            data_array = data_array[1:]
            for item in data_array:
                dic = {}
                for i, field_name in enumerate(field_array):
                    if MathClass.isnumerical(item[i]):
                        dic[field_name.upper()] = float(item[i])
                    else:
                        dic[field_name.upper()] = str(item[i]).upper()
                if StringClass.string_in_list(ImportScenario2Mongo._LocalX, dic.keys()) and \
                        StringClass.string_in_list(ImportScenario2Mongo._LocalY, dic.keys()):
                    subbsn_id = subbasin_r.get_value_by_xy(
                            dic[ImportScenario2Mongo._LocalX.upper()],
                            dic[ImportScenario2Mongo._LocalY.upper()])
                    distance = dist2stream_r.get_value_by_xy(
                            dic[ImportScenario2Mongo._LocalX.upper()],
                            dic[ImportScenario2Mongo._LocalY.upper()])
                    if subbsn_id is not None and distance is not None:
                        dic[ImportScenario2Mongo._SUBBASINID] = float(subbsn_id)
                        dic[ImportScenario2Mongo._DISTDOWN] = float(distance)
                        scenario_db[bmp_tab_name.upper()].find_one_and_replace(dic, dic,
                                                                               upsert=True)
                else:
                    scenario_db[bmp_tab_name.upper()].find_one_and_replace(dic, dic,
                                                                           upsert=True)
        # print 'BMP tables are imported.'
        # Write BMP database name into Model workflow database
        c_list = main_db.collection_names()
        if not StringClass.string_in_list(DBTableNames.main_scenario, c_list):
            main_db.create_collection(DBTableNames.main_scenario)

        bmp_info_dic = dict()
        bmp_info_dic[ImportScenario2Mongo._FLD_DB] = cfg.bmp_scenario_db
        main_db[DBTableNames.main_scenario].find_one_and_replace(bmp_info_dic, bmp_info_dic,
                                                                 upsert=True)
        return True


def main():
    """TEST CODE"""
    from seims.preprocess.config import parse_ini_configuration
    from seims.preprocess.db_mongodb import ConnectMongoDB
    seims_cfg = parse_ini_configuration()
    client = ConnectMongoDB(seims_cfg.hostname, seims_cfg.port)
    conn = client.get_conn()
    maindb = conn[seims_cfg.spatial_db]
    scenariodb = conn[seims_cfg.bmp_scenario_db]

    ImportScenario2Mongo.scenario_from_texts(seims_cfg, maindb, scenariodb)

    client.close()


if __name__ == "__main__":
    main()
