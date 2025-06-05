import os
import random
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.colors import to_hex
import matplotlib.patches as mpatches

# ========================= CẤU HÌNH ============================
# 📌 TỰ CHỌN DANH SÁCH NĂM TẠI ĐÂY:
YEARS = [2018, 2019, 2020]

# 📂 Thư mục chứa shapefile: results_camau/{năm}/coastline_{năm}.shp
SHAPE_DIR = "results_camau"
OUTPUT_PNG = "camau_shoreline_change.png"

# ====================== HÀM CHÍNH ==============================
def plot_shorelines_with_basemap():
    fig, ax = plt.subplots(figsize=(12, 12))

    color_map = {}
    patches = []
    plotted = False

    for year in YEARS:
        shp_path = os.path.join(SHAPE_DIR, str(year), f"coastline_{year}.shp")
        if not os.path.exists(shp_path):
            print(f"⚠️ Không tìm thấy: {shp_path}")
            continue

        gdf = gpd.read_file(shp_path)
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        gdf = gdf.to_crs(epsg=3857)

        # Gán màu ngẫu nhiên cho năm nếu chưa có
        color = to_hex([random.random() for _ in range(3)])
        color_map[year] = color
        gdf.boundary.plot(ax=ax, linewidth=2, edgecolor=color)
        patches.append(mpatches.Patch(color=color, label=str(year)))
        plotted = True

    if not plotted:
        print("❌ Không có dữ liệu đường bờ biển nào để hiển thị.")
        return

    # Thêm ảnh nền vệ tinh
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)

    ax.set_title("Biến động đường bờ biển tỉnh Cà Mau", fontsize=15)
    ax.legend(handles=patches, title="Năm", loc="upper right")
    ax.set_axis_off()

    # Lưu ảnh
    plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    print(f"\n✅ Đã lưu ảnh: {OUTPUT_PNG}")

    # In màu tương ứng từng năm
    print("🖍️ Chú thích màu:")
    for year, color in color_map.items():
        print(f"  Năm {year}: {color}")

    # Hiển thị
    plt.show()

# ====================== CHẠY CHÍNH =============================
if __name__ == "__main__":
    plot_shorelines_with_basemap()
