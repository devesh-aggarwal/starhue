import matplotlib.pyplot as plt
import numpy as np
import scienceplots

plt.style.use(["science", "notebook", "grid"])

wavelength = np.linspace(0.1, 1000, 1000000) * 10**(-6)

h = 6.626 * 10**(-34)
c = 2.9 * 10**8
k = 1.3806 * 10**(-23)


def spectral_radiance(T):
    x = (h * c) / (wavelength * k * T)
    radiance = np.zeros_like(wavelength, dtype=float)
    mask = x <= 700.0
    radiance[mask] = ((2 * h * c**2) / (wavelength[mask]**5)) / np.expm1(x[mask])
    return radiance


fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(wavelength * 1e9, spectral_radiance(T))
ax.set_xlabel("Wavelength (nm)")
ax.set_ylabel("Spectral radiance")
ax.set_title("Blackbody spectrum")
ax.set_xlim(left = 100, right=2000)
fig.tight_layout()


plt.show()