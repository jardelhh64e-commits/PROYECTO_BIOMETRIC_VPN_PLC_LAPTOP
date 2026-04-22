import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------
# 1. DATOS CRUDOS (TÚ PUEDES CAMBIARLOS)
# ---------------------------------------------------------

# Laptop → PLC LAN
laptop_plc = [2,3,2,3,2,3,2,3,3,3,
              2,2,3,3,2,2,3,3,2,3]

# Raspberry → PLC ETH0
rasp_plc = [0.039,0.077,0.054,0.062,0.045,
            0.055,0.048,0.071,0.059,0.066,
            0.050,0.040,0.072,0.060,0.044,
            0.058,0.049,0.077,0.039,0.054]

# Laptop → Raspberry ZT
laptop_rpi_zt = [65,339,41,89,204,191,114,90,343,299,
                 38,194,159,208,137,64,77,409,52,66]

# Laptop → PLC vía Raspberry + ZT
laptop_plc_via_zt = [81,65,54,42,142,175,28,42,326,208,
                     44,189,121,72,365,60,74,34,128,110]


# ---------------------------------------------------------
# 2. FUNCIONES
# ---------------------------------------------------------

# ======= GRÁFICA: MIN / PROM / MAX =======
def plot_min_avg_max_bars(labels, mins, avgs, maxs, title):
    x = np.arange(len(labels))
    width = 0.25

    plt.figure(figsize=(10, 6))
    plt.bar(x - width, mins, width, label='Min')
    plt.bar(x,         avgs, width, label='Promedio')
    plt.bar(x + width, maxs, width, label='Max')

    plt.title(title)
    plt.ylabel("Latencia (ms)")
    # SIN ROTACIÓN, CENTRADO
    plt.xticks(x, labels, ha='center')

    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()


# ======= GRÁFICA: RECTÁNGULOS + PROMEDIO =======
def plot_rectangle_with_avg(labels, mins, avgs, maxs, title):
    plt.figure(figsize=(10, 6))

    heights = np.array(maxs) - np.array(mins)
    bottoms = np.array(mins)

    plt.bar(
        labels,
        heights,
        bottom=bottoms,
        color="red",
        alpha=0.7,
        edgecolor="black"
    )

    for i, avg in enumerate(avgs):
        plt.plot([i - 0.3, i + 0.3], [avg, avg],
                 color="black", linewidth=2)

    plt.grid(True, which='both', axis='both',
             linestyle='--', linewidth=0.7, alpha=0.5)

    plt.title(title)
    plt.ylabel("Latencia (ms)")
    # SIN ROTACIÓN, CENTRADO
    plt.xticks(ha='center')

    plt.tight_layout()
    plt.show()


# ======= GRÁFICA: LÍNEAS SUPERPUESTAS =======
def plot_superposed_lines(series_list, labels, title):
    plt.figure(figsize=(10, 5))
    markers = ["o", "s", "^", "D"]

    for i, (serie, label) in enumerate(zip(series_list, labels)):
        plt.plot(
            range(1, len(serie)+1),
            serie,
            marker=markers[i % len(markers)],
            label=label
        )

    plt.title(title)
    plt.xlabel("Número de ping")
    plt.ylabel("Latencia (ms)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------
# 3. FIGURAS DEL ARTÍCULO
# ---------------------------------------------------------

# === FIGURAS DE LÍNEAS (LAN) ===
plot_superposed_lines(
    [laptop_plc, rasp_plc],
    ["Laptop → PLC LAN", "Raspberry → PLC ETH0"],
    title="Superposición de Latencias – Conexiones Directas (LAN)"
)

# === FIGURAS DE LÍNEAS (ZeroTier) ===
plot_superposed_lines(
    [laptop_rpi_zt, laptop_plc_via_zt],
    ["Laptop → Raspberry ZT", "Laptop → PLC vía RPi+ZT"],
    title="Superposición de Latencias – Conexiones vía ZeroTier"
)

# === BARRAS Min/Prom/Max (LAN) ===
labels_directas = [
    "Laptop → PLC\nLAN",
    "Raspberry → PLC\nETH0"
]
mins_directas = [min(laptop_plc), min(rasp_plc)]
avgs_directas = [np.mean(laptop_plc), np.mean(rasp_plc)]
maxs_directas = [max(laptop_plc), max(rasp_plc)]

plot_min_avg_max_bars(
    labels_directas,
    mins_directas,
    avgs_directas,
    maxs_directas,
    title="Conexiones Directas – Min / Prom / Max"
)

# === BARRAS Min/Prom/Max (ZeroTier) ===
labels_zt = [
    "Laptop → RPi\nZeroTier",
    "Laptop → PLC\nvía RPi+ZT"
]
mins_zt = [min(laptop_rpi_zt), min(laptop_plc_via_zt)]
avgs_zt = [np.mean(laptop_rpi_zt), np.mean(laptop_plc_via_zt)]
maxs_zt = [max(laptop_rpi_zt), max(laptop_plc_via_zt)]

plot_min_avg_max_bars(
    labels_zt,
    mins_zt,
    avgs_zt,
    maxs_zt,
    title="Conexiones ZeroTier – Min / Prom / Max"
)

# === RECTÁNGULOS (LAN) ===
plot_rectangle_with_avg(
    labels_directas,
    mins_directas,
    avgs_directas,
    maxs_directas,
    title="Rectángulos – Variabilidad de Latencia (LAN)"
)

# === RECTÁNGULOS (ZeroTier) ===
plot_rectangle_with_avg(
    labels_zt,
    mins_zt,
    avgs_zt,
    maxs_zt,
    title="Rectángulos – Variabilidad de Latencia (ZeroTier)"
)
