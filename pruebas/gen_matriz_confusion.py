import numpy as np
import matplotlib.pyplot as plt

TP, FN, FP, TN = 109, 11, 0, 120

cm = np.array([[TP, FN],
               [FP, TN]], dtype=float)

x_labels = ["Autorizado", "No autorizado"]
y_labels = ["Autorizado", "No autorizado"]

row_sums = cm.sum(axis=1, keepdims=True)
cm_pct = np.divide(cm, row_sums, out=np.zeros_like(cm), where=row_sums != 0) * 100.0

fig, ax = plt.subplots(figsize=(7.2, 5.2))

im = ax.imshow(cm, interpolation="nearest", cmap="PuBuGn", vmin=0, vmax=cm.max())

# Colorbar sin etiqueta
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("")
cbar.ax.set_ylabel("")

ax.set_xticks(np.arange(len(x_labels)))
ax.set_yticks(np.arange(len(y_labels)))
ax.set_xticklabels(x_labels, fontsize=14)
ax.set_yticklabels(y_labels, fontsize=14, rotation=90, va="center")

# Alejar etiquetas de ejes (más espacio)
ax.set_xlabel("Predicción", fontsize=18, labelpad=14)
ax.set_ylabel("Real", fontsize=18, labelpad=18)
ax.set_title("Matriz de confusión", fontsize=18, pad=12)

# Texto blanco en valores altos
threshold = cm.max() * 0.6
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        val = cm[i, j]
        txt_color = "white" if val >= threshold else "black"
        ax.text(j, i, f"{int(val)}\n{cm_pct[i, j]:.2f}%",
                ha="center", va="center", fontsize=14, color=txt_color)

# Quitar marco exterior
for spine in ax.spines.values():
    spine.set_visible(False)

# ✅ Quitar “rayitas” (ticks) de ambos ejes
ax.tick_params(axis="both", which="both", length=0)

# Sin grid
ax.grid(False)

# Ajuste de márgenes
fig.subplots_adjust(left=0.20, right=0.92, top=0.88, bottom=0.17)

plt.savefig("matriz_confusion_final.png", dpi=250)
plt.show()
