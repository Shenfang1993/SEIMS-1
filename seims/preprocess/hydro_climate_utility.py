#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Hydro-Climate utility class.
    @author   : Junzhi Liu, Liangjun Zhu
    @changelog: 13-01-10  jz - initial implementation
                17-06-23  lj - reformat according to pylint and google style
"""
import math
import time

from datetime import datetime

from seims.preprocess.text import DBTableNames, StationFields
from seims.preprocess.utility import LFs
from seims.pygeoc.pygeoc.utils.utils import StringClass, MathClass


class HydroClimateUtilClass(object):
    """Hydro-Climate utility functions."""

    def __init__(self):
        """Empty"""
        pass

    @staticmethod
    def dr(doy):
        """earth-sun distance"""
        return 1. + 0.033 * math.cos(2. * math.pi * doy / 365.)

    @staticmethod
    def dec(doy):
        """Declination."""
        return 0.409 * math.sin(2. * math.pi * doy / 365. - 1.39)

    @staticmethod
    def ws(lat, dec):
        """sunset hour angle"""
        x = 1. - math.pow(math.tan(lat), 2.) * math.pow(math.tan(dec), 2.)
        if x < 0:
            x = 0.00001
        # print x
        return 0.5 * math.pi - math.atan(-math.tan(lat) * math.tan(dec) / math.sqrt(x))

    @staticmethod
    def rs(doy, n, lat):
        """solar radiation, n is sunshine duration"""
        lat = lat * math.pi / 180.
        a = 0.25
        b = 0.5
        d = HydroClimateUtilClass.dec(doy)
        w = HydroClimateUtilClass.ws(lat, d)
        nn = 24. * w / math.pi
        # Extraterrestrial radiation for daily periods
        ra = (24. * 60. * 0.082 * HydroClimateUtilClass.dr(doy) / math.pi) * \
             (w * math.sin(lat) * math.sin(d) + math.cos(lat) * math.cos(d) * math.sin(w))
        return (a + b * n / nn) * ra

    @staticmethod
    def query_climate_sites(clim_db, site_type):
        """Query climate sites information, return a dict with stationID as key."""
        from seims.preprocess.db_import_sites import SiteInfo
        sites_loc = dict()
        sites_coll = clim_db[DBTableNames.sites]
        find_results = sites_coll.find({StationFields.type: site_type})
        for dic in find_results:
            sites_loc[dic[StationFields.id]] = SiteInfo(dic[StationFields.id],
                                                        dic[StationFields.name],
                                                        dic[StationFields.lat],
                                                        dic[StationFields.lon],
                                                        dic[StationFields.x],
                                                        dic[StationFields.y],
                                                        dic[StationFields.elev])
        return sites_loc

    @staticmethod
    def get_datetime_from_string(formatted_str):
        """get datetime() object from string formatted %Y-%m-%d %H:%M:%S"""
        try:
            org_time = time.strptime(formatted_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("The format of DATETIME must be %Y-%m-%d %H:%M:%S!")
        return datetime(org_time.tm_year, org_time.tm_mon, org_time.tm_mday,
                        org_time.tm_hour, org_time.tm_min, org_time.tm_sec)

    @staticmethod
    def get_time_system_from_data_file(in_file):
        """Get the time system from the data file. The basic format is:
           #<time_system> [<time_zone>], e.g., #LOCALTIME 8, #UTCTIME
        """
        time_sys = 'LOCALTIME'
        time_zone = time.timezone / -3600
        f = open(in_file)
        for line in f:
            str_line = line
            for LF in LFs:
                if LF in line:
                    str_line = line.split(LF)[0]
                    break
            if str_line[0] != '#':
                break
            if str_line.lower().find('utc') >= 0:
                time_sys = 'UTCTIME'
                time_zone = 0
                break
            if str_line.lower().find('local') >= 0:
                line_list = StringClass.split_string(str_line, [','])
                if len(line_list) == 2 and MathClass.isnumerical(line_list[1]):
                    time_zone = -1 * int(line_list[1])
                break
        f.close()
        return time_sys, time_zone


def main():
    """TEST CODE"""
    from seims.preprocess.config import parse_ini_configuration
    from seims.preprocess.db_mongodb import ConnectMongoDB
    seims_cfg = parse_ini_configuration()
    client = ConnectMongoDB(seims_cfg.hostname, seims_cfg.port)
    conn = client.get_conn()
    hydroclim_db = conn[seims_cfg.climate_db]

    site_m = HydroClimateUtilClass.query_climate_sites(hydroclim_db, 'M')
    site_p = HydroClimateUtilClass.query_climate_sites(hydroclim_db, 'P')

    client.close()


if __name__ == "__main__":
    main()
