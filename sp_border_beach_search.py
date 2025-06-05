import os
import sys
import json
import logging
import datetime
import requests
import zipfile
import shutil
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import box, mapping
import geopandas as gpd
from tqdm import tqdm

# ----------------------------- LOGGER -----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# --------------------------- CẤU HÌNH ----------------------------
SAVE_DIR = os.path.abspath("results_camau")
DOWNLOAD_DIR = os.path.join(SAVE_DIR, "downloaded_SAFE")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------------------- HÀM HỖ TRỢ -------------------------------

def get_camau_geometry():
    minx, miny = 104.5, 8.5
    maxx, maxy = 105.5, 9.7
    return f"POLYGON(({minx} {maxy},{maxx} {maxy},{maxx} {miny},{minx} {miny},{minx} {maxy}))"

def search_sentinel2_scenes(year, cloud_cover=20):
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    aoi = get_camau_geometry()

    query = (
        f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
        f"$filter=Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI1C') and "
        f"ContentDate/Start gt {start}T00:00:00.000Z and "
        f"ContentDate/Start lt {end}T23:59:59.999Z and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {cloud_cover}) and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{aoi}')"
        f"&$expand=Assets&$orderby=ContentDate/Start desc&$top=50"
    )

    response = requests.get(query)
    if response.status_code != 200:
        logger.error(f"Lỗi API: {response.status_code} - {response.text}")
        return []

    items = response.json().get("value", [])
    results = []

    for item in items:
        name = item.get("Name")
        download_link = item.get("Assets", [{}])[0].get("DownloadLink")
        cloud = None

        if "Attributes" in item:
            for att in item["Attributes"]:
                if att["Name"] == "cloudCover":
                    cloud = att["Value"]

        results.append({
            "id": item.get("Id"),
            "name": name,
            "cloud": cloud if cloud is not None else 100.0,  # nếu không có cloudCover thì để 100%
            "download_link": download_link
        })

    return results


def download_safe_zip(scene, year_folder):
    url = scene["download_link"]
    logger.warning(f"💡 Link tải thủ công: {url}")
    logger.warning("👉 Hãy tải file .SAFE này về máy và đặt vào thư mục tương ứng để tiếp tục xử lý.")

    expected_safe_dir = os.path.join(year_folder, f"{scene['name']}.SAFE")

    if os.path.exists(expected_safe_dir):
        logger.info(f"✅ Đã phát hiện file .SAFE: {expected_safe_dir}")
        return expected_safe_dir
    else:
        logger.error(f"❌ Chưa có thư mục {expected_safe_dir}. Hãy tải và giải nén .SAFE vào đây.")
        sys.exit(1)


def find_band_paths(safe_folder):
    import glob
    b03 = glob.glob(os.path.join(safe_folder, "**/*B03*.jp2"), recursive=True)
    b08 = glob.glob(os.path.join(safe_folder, "**/*B08*.jp2"), recursive=True)
    return b03[0] if b03 else None, b08[0] if b08 else None

def compute_ndwi(b03_path, b08_path, output_path):
    with rasterio.open(b03_path) as green, rasterio.open(b08_path) as nir:
        green_data = green.read(1).astype("float32")
        nir_data = nir.read(1).astype("float32")
        ndwi = (green_data - nir_data) / (green_data + nir_data)
        ndwi[np.isinf(ndwi)] = np.nan
        profile = green.profile
        profile.update(dtype="float32", count=1)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(ndwi, 1)
    return output_path

def process_year(year, auto_open=False):
    logger.info(f"\n📅 Xử lý năm {year}")
    year_dir = os.path.join(SAVE_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    scenes = search_sentinel2_scenes(year)
    if not scenes:
        logger.warning("❌ Không tìm thấy ảnh phù hợp.")
        return

    # Chọn ảnh có mây thấp nhất
    best = min(scenes, key=lambda s: s["cloud"])
    logger.info(f"✅ Ảnh tốt nhất: {best['name']} - Mây: {best['cloud']}%")

    safe_path = download_safe_zip(best, year_dir)
    b03, b08 = find_band_paths(safe_path)
    if not b03 or not b08:
        logger.error("Không tìm thấy băng B03 hoặc B08.")
        return

    ndwi_path = os.path.join(year_dir, f"NDWI_{year}.tif")
    compute_ndwi(b03, b08, ndwi_path)

    if auto_open:
        with rasterio.open(ndwi_path) as src:
            plt.imshow(src.read(1), cmap="Blues")
            plt.title(f"NDWI - {year}")
            plt.colorbar()
            plt.show()

def main():
    for year in range(2018, 2021):
        process_year(year, auto_open=True)

if __name__ == "__main__":
    main()
