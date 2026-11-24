
import wfdb
import numpy as np
import matplotlib.pyplot as plt

# Step 1
# Load ECG recording
record = wfdb.rdrecord('mitdb/100')

# Display information
print("Sampling Frequency:", record.fs)
print("Signal Channels:", record.sig_name)
print("Total Samples:", len(record.p_signal))


# Load ECG annotations
ann = wfdb.rdann('mitdb/100', 'atr')

# Print first 10 annotation positions
print("Annotation Positions:", ann.sample[:10])

# Print first 10 annotation symbols
print("Annotation Symbols:", ann.symbol[:10])


# Select first ECG channel (MLII)
ecg = record.p_signal[:, 0]

# Take first 10 seconds of ECG
duration = 10
total_samples = int(duration * record.fs)

ecg = ecg[:total_samples]
clean_ecg = ecg.copy()

# Select heartbeat annotations

beat_symbols = [
    'N', 'L', 'R', 'B', 'A', 'a',
    'J', 'S', 'V', 'r', 'F', 'e',
    'j', 'n', 'E', '/', 'f', 'Q'
]

# Convert annotation data into arrays
samples = np.array(ann.sample)
symbols = np.array(ann.symbol)

# Select only heartbeat annotations
mask = np.isin(symbols, beat_symbols)

r_peaks = samples[mask]

# Select peaks within first 10 seconds
r_peaks = r_peaks[r_peaks < total_samples]


# Create time axis


time = np.arange(len(ecg)) / record.fs


# Plot ECG signal

plt.figure(figsize=(12, 4))

# Draw ECG waveform
plt.plot(time, ecg, label='ECG Signal')

# Mark original R-peaks
plt.scatter(
    r_peaks / record.fs,
    ecg[r_peaks],
    color='red',
    label='Original R-peaks',
    s=40,
    zorder=5
)

plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude (mV)")
plt.title("ECG Signal - Record 100 (MLII)")

plt.legend()
plt.grid()

# Save annotated graph
plt.savefig("ECG_Record_100_Annotated.png", dpi=300)



# Step 2: Add 50 Hz Powerline Noise and baseline drift

fs = record.fs

t = np.arange(len(clean_ecg)) / fs

# 50 Hz Powerline Noise
powerline_noise = 0.1 * np.sin(2 * np.pi * 50 * t)

# Add baseline drift
baseline_drift = 0.2 * np.sin(2 * np.pi * 0.3 *t)

noisy_ecg = clean_ecg + powerline_noise + baseline_drift

print("Noise added successfully!")


plt.figure(figsize=(12, 4))

plt.plot(t, noisy_ecg, label="Noisy ECG", color="orange")

plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude (mV)")
plt.title("ECG Signal with 50 Hz Powerline Noise and Baseline Drift")

plt.legend()
plt.grid()

plt.savefig("ECG_50Hz_Noisy.png", dpi=300)

plt.show()




# STEP 3: BANDPASS FILTERING

from scipy.signal import butter, sosfiltfilt

# Cutoff frequencies
lowcut = 0.5
highcut = 100

# Filter order
order = 4

# Design Bandpass Filter
sos = butter(
    order,
    [lowcut, highcut],
    btype='bandpass',
    fs=fs,
    output='sos'
)

# Apply filter
bandpass_ecg = sosfiltfilt(sos, noisy_ecg)

print("Bandpass filtering completed!")


# Plot noisy and filtered ECG

plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(t, noisy_ecg, color='orange')
plt.title("Noisy ECG")
plt.ylabel("Amplitude (mV)")
plt.grid()

plt.subplot(2, 1, 2)
plt.plot(t, bandpass_ecg, color='blue')
plt.title("After Bandpass Filtering")
plt.xlabel("Time (seconds)")
plt.ylabel("Amplitude (mV)")
plt.grid()

plt.tight_layout()

plt.savefig("ECG_Bandpass_Filtered.png", dpi=300)

plt.show()



# STEP 4: NOTCH FILTERING

from scipy.signal import iirnotch, filtfilt

# Notch filter parameters
notch_freq = 50
quality_factor = 30

# Design Notch Filter
b, a = iirnotch(
    notch_freq,
    quality_factor,
    fs=fs
)

# Apply Notch Filter
notch_ecg = filtfilt(
    b,
    a,
    bandpass_ecg
)

print("Notch filtering completed!")


# Plot Notch Filtered ECG
plt.figure(figsize=(14, 5))

plt.plot(
    t,
    notch_ecg,
    color='green',
    linewidth=0.8,
    label='Notch Filtered ECG'
)

plt.title('ECG Signal After 50 Hz Notch Filtering')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude (mV)')
plt.legend()
plt.grid(True)

# Save graph
plt.savefig(
    'notch_filtered_ecg.png',
    dpi=300,
    bbox_inches='tight'
)

plt.show()

print("Notch filtered ECG graph saved successfully!")



# STEP 6: BEFORE AND AFTER FILTERING COMPARISON



# Select first 5 seconds for clear visualization
samples = min(len(t), int(5 * fs))

plt.figure(figsize=(14, 6))

plt.plot(
    t[:samples],
    clean_ecg[:samples],
    color='black',
    linewidth=1,
    label='Original Clean ECG'
)

plt.plot(
    t[:samples],
    noisy_ecg[:samples],
    color='blue',
    alpha=0.6,
    linewidth=0.8,
    label='Noisy ECG'
)

plt.plot(
    t[:samples],
    notch_ecg[:samples],
    color='green',
    linewidth=1,
    label='Filtered ECG'
)

plt.title('ECG Before and After Filtering')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude (mV)')
plt.legend()
plt.grid(True)

plt.savefig(
    'before_after_comparison.png',
    dpi=300,
    bbox_inches='tight'
)

plt.show()


# STEP 7: SNR CALCULATION AT ALL STAGES

def calculate_snr(reference, test_signal, trim=int(1 * fs)):
    ref = reference[trim:-trim]
    test = test_signal[trim:-trim]

    ref = ref - ref.mean()
    test = test - test.mean()

    noise = test - ref

    signal_power = np.mean(ref ** 2)
    noise_power = np.mean(noise ** 2)

    return 10 * np.log10(signal_power / noise_power)

# SNR at each stage (sabka reference clean_ecg)
snr_raw = calculate_snr(clean_ecg, noisy_ecg)
snr_bandpass = calculate_snr(clean_ecg, bandpass_ecg)
snr_notch = calculate_snr(clean_ecg, notch_ecg)

# Improvements
bandpass_improvement = snr_bandpass - snr_raw
notch_improvement = snr_notch - snr_bandpass
total_improvement = snr_notch - snr_raw

# Display results
print("SNR of Original Noisy ECG:", round(snr_raw, 2), "dB")
print("SNR After Bandpass:", round(snr_bandpass, 2), "dB")
print("SNR After Bandpass + Notch:", round(snr_notch, 2), "dB")

print("Bandpass Improvement:", round(bandpass_improvement, 2), "dB")
print("Notch Improvement:", round(notch_improvement, 2), "dB")
print("Total SNR Improvement:", round(total_improvement, 2), "dB")


# STEP 8: COMPARISON OF ALL FILTERING STAGES

import matplotlib.pyplot as plt

# Select first 5 seconds
samples = min(len(t), int(5 * fs))

plt.figure(figsize=(15, 7))

# Original Clean ECG
plt.plot(
    t[:samples],
    clean_ecg[:samples],
    color='black',
    linewidth=1,
    label='Original Clean ECG'
)

# Noisy ECG
plt.plot(
    t[:samples],
    noisy_ecg[:samples],
    color='blue',
    alpha=0.5,
    linewidth=0.8,
    label='Noisy ECG'
)

# After Bandpass Filter
plt.plot(
    t[:samples],
    bandpass_ecg[:samples],
    color='orange',
    linewidth=1,
    label='After Bandpass Filter'
)

# After Bandpass + Notch Filter
plt.plot(
    t[:samples],
    notch_ecg[:samples],
    color='green',
    linewidth=1,
    label='After Bandpass + Notch Filter'
)

plt.title('ECG Signal: Comparison of All Filtering Stages')
plt.xlabel('Time (seconds)')
plt.ylabel('Amplitude (mV)')
plt.legend()
plt.grid(True)

# Save graph
plt.savefig(
    'all_filtering_stages.png',
    dpi=300,
    bbox_inches='tight'
)

plt.show()

print("All filtering stages comparison graph saved!")


