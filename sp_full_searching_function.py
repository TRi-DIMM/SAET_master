import os
import sys
import logging
import logging.handlers
import webbrowser

import sp_config  # cần để đọc biến môi trường .env

from sp_parameters_validation import parse_args_searching, checkCommandArgummentsSearching
from sp_searching_functions import (searchS2CDSE,
                                    writeHtmlS2CDSE,
                                    searchLandsat8,
                                    writeHtmlLandsat8,
                                    writeTextS2CDSE,
                                    writeTextLandsat)
from sp_basic_functions import createBasicFolderStructure, findIntoFolderStructure


logger = logging.getLogger("")


def init_logger(level):
    if level == '10':
        log_level = logging.DEBUG
    elif level == '20':
        log_level = logging.INFO
    elif level == '30':
        log_level = logging.WARNING
    elif level == '40':
        log_level = logging.ERROR
    elif level == '50':
        log_level = logging.CRITICAL
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    if log_level in [logging.INFO, logging.WARNING]:
        console_formatting = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    else:
        console_formatting = logging.Formatter('%(asctime)s %(filename)s-%(funcName)s %(levelname)s %(message)s')

    console_handler.setFormatter(console_formatting)
    logger.addHandler(console_handler)


def run_full_search(args):
    # kiểm tra và phân tích đối số đầu vào
    run_parameters = checkCommandArgummentsSearching(args)

    # lấy thông tin từ biến môi trường
    user_esa = os.getenv('USER_ESA')
    pass_esa = os.getenv('PASS_ESA')
    user_usgs = os.getenv('USER_USGS')
    pass_usgs = os.getenv('PASS_USGS')
    beaches_path = os.getenv('SHP_BEACHES_PATH')
    l8grid_path = os.getenv('SHP_LANDSAT_GRID_PATH')
    s2grid_path = os.getenv('SHP_SENTINEL2_GRID_PATH')
    saet_home_path = os.getenv('SAET_HOME_PATH')

    # kiểm tra shapefile
    if not os.path.isfile(l8grid_path):
        logger.error(f'Lỗi: Không tìm thấy file {l8grid_path}')
        sys.exit(1)
    if not os.path.isfile(s2grid_path):
        logger.error(f'Lỗi: Không tìm thấy file {s2grid_path}')
        sys.exit(1)

    # cập nhật vào run_parameters
    run_parameters.update({
        'user_esa': user_esa,
        'pass_esa': pass_esa,
        'user_usgs': user_usgs,
        'pass_usgs': pass_usgs,
        'l8grid_path': l8grid_path,
        's2grid_path': s2grid_path
    })

    # tạo thư mục và đường dẫn kết quả
    createBasicFolderStructure(base_path=saet_home_path)
    output_folder = findIntoFolderStructure(base_path=saet_home_path, folder_name='search_data')
    run_parameters['output_search_folder'] = output_folder

    html_file = None

    # tìm kiếm Sentinel-2
    if run_parameters['s2_product'] != 'NONE':
        s2_scenes = searchS2CDSE(run_parameters)
        html_file = writeHtmlS2CDSE(s2_scenes, output_folder)
        writeTextS2CDSE(s2_scenes, output_folder)

    # tìm kiếm Landsat
    if run_parameters['l8_product'] != 'NONE':
        l8_scenes = searchLandsat8(run_parameters)
        html_file = writeHtmlLandsat8(l8_scenes, output_folder)
        writeTextLandsat(l8_scenes, output_folder)

    # mở kết quả cuối cùng
    if html_file and os.path.isfile(html_file):
        logger.info(f'📂 Mở kết quả tìm kiếm: {html_file}')
        webbrowser.open(html_file)
    else:
        logger.warning('❗ Không tìm thấy file HTML kết quả để mở.')


if __name__ == '__main__':
    args = parse_args_searching()
    log_level = os.getenv('LOG_LEVEL', '20')  # default INFO
    init_logger(log_level)
    logger.info('📌 Bắt đầu chạy sp_full_searching_function.py')
    run_full_search(args)
    logger.info('✅ Hoàn tất tìm kiếm hình ảnh theo yêu cầu.')
    sys.exit(0)
