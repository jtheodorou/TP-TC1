"""
polos_ceros_RLC.py
──────────────────
Diagrama de polos y ceros para los 4 circuitos RLC del TP Final TC1.

  Circuito 2 – Pasa-Bajos  (LP):         salida en C
  Circuito 3 – Pasa-Altos  (HP):         salida en L
  Circuito 4 – Pasa-Banda  (BP):         salida en R
  Circuito 5 – Rechaza-Banda (Notch/BS): salida en serie L+C

Funciones de transferencia (denominador común: LC·s² + RC·s + 1):
  Circ.2:  H(s) =      1      / (LC·s² + RC·s + 1)
  Circ.3:  H(s) =    LC·s²    / (LC·s² + RC·s + 1)
  Circ.4:  H(s) =    RC·s     / (LC·s² + RC·s + 1)
  Circ.5:  H(s) = (LC·s²+1)  / (LC·s² + RC·s + 1)
"""

import os
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# ══════════════════════════════════════════════════════════════════════════════
#  PARÁMETROS 
# ══════════════════════════════════════════════════════════════════════════════
R = 50       # Ω
L = 1e-3     # H   
C = 10e-9     # F  
# ══════════════════════════════════════════════════════════════════════════════

KS = 1e3   # escala visual: todo en krad/s

omega0 = 1.0 / np.sqrt(L * C)
Q      = np.sqrt(L / C) / R

print("─" * 58)
print(f"  R = {R} Ω   L = {L*1e3:.4g} mH   C = {C*1e9:.4g} nF")
print(f"  ω₀ = {omega0/KS:.4f} krad/s  ({omega0/(2*np.pi):.2f} Hz)")
print(f"  Q  = {Q:.4f}  → {'subamortiguado (polos complejos)' if Q > 0.5 else 'sobreamortiguado (polos reales)'}")
print("─" * 58)

# ─── Denominador común: LC·s² + RC·s + 1 ─────────────────────────────────
den = np.array([L*C, R*C, 1.0])

# ─── Circuitos: (numerador, tipo, etiqueta subplot, H(s) a mostrar) ────────
circuits = [
    (np.array([1.0]),
     "LP · Pasa-Bajos",
     "Circ.2  –  salida en $C$",
     r"$H(s)=\frac{1}{LCs^2+RCs+1}$"),

    (np.array([L*C, 0.0, 0.0]),
     "HP · Pasa-Altos",
     "Circ.3  –  salida en $L$",
     r"$H(s)=\frac{LCs^2}{LCs^2+RCs+1}$"),

    (np.array([R*C, 0.0]),
     "BP · Pasa-Banda",
     "Circ.4  –  salida en $R$",
     r"$H(s)=\frac{RCs}{LCs^2+RCs+1}$"),

    (np.array([L*C, 0.0, 1.0]),
     "BS · Rechaza-Banda (Notch)",
     "Circ.5  –  salida en $L{+}C$",
     r"$H(s)=\frac{LCs^2+1}{LCs^2+RCs+1}$"),
]

# ─── Polos (comunes a todos) ───────────────────────────────────────────────
poles_k = np.roots(den) / KS

print("\nPolos (comunes a los 4 circuitos):")
for p in sorted(poles_k, key=lambda x: -x.imag):
    print(f"  p = {p.real:+.3f}  {'+' if p.imag >= 0 else ''}{p.imag:.3f}j   krad/s")


# ─── Utilidades ────────────────────────────────────────────────────────────

def calc_zeros(num: np.ndarray) -> np.ndarray:
    """Ceros finitos del numerador, en krad/s."""
    if num.size <= 1:
        return np.array([], dtype=complex)
    return np.roots(num).astype(complex) / KS


def merge_zeros(zs: np.ndarray, tol: float):
    """Agrupa ceros numericamente coincidentes → [(valor, multiplicidad)]."""
    groups: list = []
    for z in zs:
        for g in groups:
            if abs(z - g[0]) < tol:
                g[1] += 1
                break
        else:
            groups.append([z, 1])
    return [(g[0], g[1]) for g in groups]


# ─── Colores ────────────────────────────────────────────────────────────────
CP = '#c0392b'   # rojo  – polos
CZ = '#1a5276'   # azul  – ceros
CA = '#1c2833'   # negro – ejes

# ─── Figura 2×2 ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.patch.set_facecolor('#f0f3f4')
axes = axes.flatten()

for ax, (num, ftype, clabel, hexpr) in zip(axes, circuits):

    zeros_k = calc_zeros(num)

    print(f"\nCeros  –  {ftype}:")
    if zeros_k.size == 0:
        print("  (sin ceros finitos; H → 0 para s → ∞)")
    for z in sorted(zeros_k, key=lambda x: -x.imag):
        print(f"  z = {z.real:+.3f}  {'+' if z.imag >= 0 else ''}{z.imag:.3f}j   krad/s")

    # ── Límites del plano ──────────────────────────────────────────────────
    all_k = np.concatenate([poles_k, zeros_k]) if zeros_k.size else poles_k
    ref   = max(np.abs(all_k).max(), omega0 / KS) * 1.75

    ax.set_facecolor('#fafbff')
    ax.set_xlim(-ref, ref)
    ax.set_ylim(-ref, ref)
    ax.set_aspect('equal')
    ax.axhline(0, color=CA, lw=0.9, zorder=1)
    ax.axvline(0, color=CA, lw=0.9, zorder=1)
    ax.grid(True, ls=':', alpha=0.40, color='#aaa')

    # ── Polos (×) ──────────────────────────────────────────────────────────
    for p in poles_k:
        ax.plot(p.real, p.imag, 'x',
                color=CP, ms=14, mew=2.5, zorder=5)

    # anotar solo el polo del semiplano superior (el inferior es conjugado)
    for p in poles_k:
        if p.imag > 1e-8:
            sign = '+' if p.imag >= 0 else ''
            ann = f"({p.real:.1f}, {sign}{p.imag:.1f}j)"
            ax.annotate(ann, xy=(p.real, p.imag), xytext=(7, 5),
                        textcoords='offset points', fontsize=7.5, color=CP,
                        bbox=dict(boxstyle='round,pad=0.25', fc='w',
                                  ec=CP, lw=0.7, alpha=0.88))

    # ── Ceros (○) con multiplicidad ────────────────────────────────────────
    for z, mult in merge_zeros(zeros_k, tol=ref * 1e-5):
        ax.plot(z.real, z.imag, 'o',
                mec=CZ, mfc='none', ms=12, mew=2.2, zorder=5)
        sign = '+' if z.imag >= 0 else ''
        ann  = f"({z.real:.1f}, {sign}{z.imag:.1f}j)"
        if mult > 1:
            ann += f"  ×{mult}"
        # posicionar etiqueta según cuadrante
        dy = 5 if z.imag > -ref * 0.15 else -24
        ax.annotate(ann, xy=(z.real, z.imag), xytext=(7, dy),
                    textcoords='offset points', fontsize=7.5, color=CZ,
                    bbox=dict(boxstyle='round,pad=0.25', fc='w',
                              ec=CZ, lw=0.7, alpha=0.88))

    ax.set_xlabel("σ  [krad/s]", fontsize=9)
    ax.set_ylabel("jω  [krad/s]", fontsize=9)
    ax.set_title(f"{clabel}  —  {ftype}", fontsize=10.5, fontweight='bold', pad=5)

    # H(s) en esquina inferior derecha
    ax.text(0.97, 0.03, hexpr,
            transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.35', fc='#fef9e7',
                      ec='#bdc3c7', alpha=0.92))

# ─── Leyenda global ─────────────────────────────────────────────────────────
fig.legend(
    handles=[
        Line2D([0], [0], marker='x', ls='none',
               mec=CP, ms=12, mew=2.5, label='Polo  (×)'),
        Line2D([0], [0], marker='o', ls='none',
               mec=CZ, mfc='none', ms=10, mew=2.2, label='Cero  (○)'),
    ],
    loc='upper center', ncol=2, fontsize=11,
    bbox_to_anchor=(0.5, 1.005), framealpha=0.93, edgecolor='#bbb'
)

# ─── Título principal ───────────────────────────────────────────────────────
upper_p = poles_k[poles_k.imag > 0.0][0] if np.any(poles_k.imag > 0) else poles_k[0]
pole_str = (f"$s = {upper_p.real:.2f} \\pm j\\,{abs(upper_p.imag):.2f}$ krad/s"
            if np.any(poles_k.imag > 0) else
            f"$s = {poles_k[0].real:.2f},\\; {poles_k[1].real:.2f}$ krad/s")

fig.suptitle(
    f"Diagrama de Polos y Ceros  –  Circuitos RLC Serie\n"
    f"R = {R} Ω,   L = {L*1e3:.0f} mH,   C = {C*1e9:.1f} nF   "
    f"($\\omega_0 = {omega0/KS:.3f}$ krad/s,   $Q = {Q:.3f}$)\n"
    f"Polos comunes: {pole_str}",
    fontsize=11.5, fontweight='bold', y=1.07
)

plt.tight_layout(pad=2.0)

output_dir = os.path.dirname(os.path.abspath(__file__))
fname = os.path.join(output_dir, "polos_ceros_RLC.png")
plt.savefig(fname, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
print(f"\n✓  Figura guardada: {fname}")
