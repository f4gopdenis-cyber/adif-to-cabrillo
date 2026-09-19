import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from datetime import datetime

APP_TITLE = "ADIF → Cabrillo - F4GOP"

BAND_TO_KHZ = {
    "160m": "1800", "80m": "3500", "60m": "5000", "40m": "7000",
    "30m": "10000", "20m": "14000", "17m": "18000", "15m": "21000",
    "12m": "24000", "10m": "28000", "6m": "50", "4m": "70",
    "2m": "144", "70cm": "432", "23cm": "1296"
}

def parse_adif(text):
    """Read standard ADIF records terminated by <EOR>."""
    records = []
    for raw in re.split(r"<EOR\s*>", text, flags=re.I):
        if "<" not in raw:
            continue
        fields = {}
        # ADIF field: <NAME:length[:type]>value
        pat = re.compile(r"<([A-Za-z0-9_]+):(\d+)(?::[^>]+)?>", re.I)
        matches = list(pat.finditer(raw))
        for i, m in enumerate(matches):
            name = m.group(1).upper()
            length = int(m.group(2))
            start = m.end()
            value = raw[start:start+length]
            fields[name] = value.strip()
        if "CALL" in fields and "QSO_DATE" in fields:
            records.append(fields)
    return records

def clean_call(call):
    return re.sub(r"[^A-Z0-9/]", "", call.upper())

def cab_mode(mode, submode=""):
    mode = (mode or "").upper()
    submode = (submode or "").upper()
    if mode == "CW":
        return "CW"
    if mode in ("SSB", "USB", "LSB", "AM", "FM", "PHONE"):
        return "PH"
    if mode in ("RTTY", "PSK", "PSK31", "PSK63", "PSK125", "FT8",
                "FT4", "JT65", "JT9", "JS8", "FSK", "DIGI"):
        return "RY"
    if submode.startswith("PSK") or "RTTY" in submode:
        return "RY"
    if mode == "DIGITAL":
        return "RY"
    return mode[:2] if mode else "PH"

def frequency(rec):
    f = rec.get("FREQ", "").strip()
    if f:
        try:
            # ADIF FREQ is MHz; Cabrillo wants kHz for HF.
            khz = int(round(float(f) * 1000))
            return str(khz)
        except ValueError:
            pass
    band = rec.get("BAND", "").strip().lower()
    return BAND_TO_KHZ.get(band, "0000")

def rst_for(rec, sent=True):
    key = "RST_SENT" if sent else "RST_RCVD"
    value = rec.get(key, "").strip()
    if value:
        return value
    # If a logger omitted received RST, do not invent a signal report.
    return ""

def make_qso(rec, own_call, sent_exchange="", received_exchange=""):
    date = rec.get("QSO_DATE", "").strip()
    if len(date) == 8 and date.isdigit():
        date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
    else:
        return None

    t = rec.get("TIME_ON", "").strip()
    t = re.sub(r"[^0-9]", "", t)[:4].ljust(4, "0")
    call = clean_call(rec.get("CALL", ""))
    if not call:
        return None

    own_call = clean_call(own_call)
    if not own_call:
        return None

    freq = frequency(rec)
    mode = cab_mode(rec.get("MODE", ""), rec.get("SUBMODE", ""))
    rs = rst_for(rec, True)
    rr = rst_for(rec, False)

    # Cabrillo's exchange is contest-specific. The GUI lets the operator
    # provide fixed sent/received exchanges when the ADIF has none.
    # Empty exchanges are retained as empty fields rather than invented.
    # Format: QSO: freq mode date time MYCALL sentRST sentExch HISCALL rcvdRST rcvdExch t
    return f"QSO: {freq:>5} {mode:<2} {date} {t} {own_call:<13} {rs:<3} {sent_exchange:<6} {call:<13} {rr:<3} {received_exchange:<6} 0"

def convert_file(source, destination, header):
    text = Path(source).read_text(encoding="utf-8", errors="replace")
    records = parse_adif(text)
    if not records:
        raise ValueError("Aucun QSO ADIF valide n'a été trouvé.")

    qsos = []
    skipped = 0
    for rec in records:
        line = make_qso(rec, header["callsign"], header["sent_exchange"], header["received_exchange"])
        if line:
            qsos.append((rec.get("QSO_DATE",""), rec.get("TIME_ON",""), line))
        else:
            skipped += 1

    qsos.sort(key=lambda x: (x[0], x[1]))

    lines = [
        "START-OF-LOG: 3.0",
        f"CONTEST: {header['contest']}",
        f"CALLSIGN: {header['callsign']}",
        f"OPERATORS: {header['callsign']}",
        "CATEGORY-OPERATOR: SINGLE-OP",
        "CATEGORY-TRANSMITTER: ONE",
        "CATEGORY-ASSISTED: NON-ASSISTED",
        "CATEGORY-BAND: ALL",
        f"CATEGORY-POWER: {header['power']}",
        f"CATEGORY-MODE: {header['category_mode']}",
        "CATEGORY-STATION: FIXED",
        f"NAME: {header['name']}",
        f"ADDRESS: {header['address']}",
        f"ADDRESS-CITY: {header['city']}",
        f"ADDRESS-COUNTRY: {header['country']}",
        "",
    ]
    lines.extend(q[2] for q in qsos)
    lines.append("END-OF-LOG:")
    Path(destination).write_text("\n".join(lines) + "\n", encoding="ascii", errors="replace")
    return len(records), len(qsos), skipped

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("760x650")
        root.minsize(700, 600)

        self.source = tk.StringVar()
        self.destination = tk.StringVar()
        self.contest = tk.StringVar(value="CONTEST")
        self.callsign = tk.StringVar()
        self.power = tk.StringVar(value="HIGH")
        self.category_mode = tk.StringVar(value="CW")
        self.name = tk.StringVar()
        self.address = tk.StringVar()
        self.city = tk.StringVar()
        self.country = tk.StringVar()
        self.sent_exchange = tk.StringVar()
        self.received_exchange = tk.StringVar()

        frame = ttk.Frame(root, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="ADIF → CABRILLO", font=("Segoe UI", 18, "bold")).pack(pady=(0,12))

        f = ttk.LabelFrame(frame, text="1 - Fichier ADIF", padding=10)
        f.pack(fill="x", pady=5)
        ttk.Entry(f, textvariable=self.source).pack(side="left", fill="x", expand=True)
        ttk.Button(f, text="Ouvrir...", command=self.open_source).pack(side="left", padx=(8,0))

        f = ttk.LabelFrame(frame, text="2 - Paramètres Cabrillo", padding=10)
        f.pack(fill="x", pady=5)

        rows = [
            ("Concours", self.contest),
            ("Indicatif", self.callsign),
            ("Puissance", self.power),
            ("Catégorie mode", self.category_mode),
            ("Nom", self.name),
            ("Adresse", self.address),
            ("Ville", self.city),
            ("Pays", self.country),
            ("Échange envoyé", self.sent_exchange),
            ("Échange reçu", self.received_exchange),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(f, text=label, width=20).grid(row=i//2, column=(i%2)*2, sticky="w", padx=5, pady=4)
            ttk.Entry(f, textvariable=var, width=28).grid(row=i//2, column=(i%2)*2+1, sticky="ew", padx=5, pady=4)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(3, weight=1)

        note = ("Important : l'échange Cabrillo dépend du concours. "
                "Si ton ADIF ne contient pas l'échange du concours, renseigne-le ici. "
                "Le programme ne l'invente pas.")
        ttk.Label(frame, text=note, wraplength=700).pack(anchor="w", pady=8)

        f = ttk.LabelFrame(frame, text="3 - Fichier Cabrillo", padding=10)
        f.pack(fill="x", pady=5)
        ttk.Entry(f, textvariable=self.destination).pack(side="left", fill="x", expand=True)
        ttk.Button(f, text="Enregistrer sous...", command=self.choose_destination).pack(side="left", padx=(8,0))

        ttk.Button(frame, text="CONVERTIR ADIF → CABRILLO", command=self.convert,
                   padding=10).pack(pady=15)

        self.status = tk.StringVar(value="Prêt.")
        ttk.Label(frame, textvariable=self.status, wraplength=700).pack(anchor="w")

        self.preview = tk.Text(frame, height=12, width=90)
        self.preview.pack(fill="both", expand=True, pady=(8,0))

    def open_source(self):
        p = filedialog.askopenfilename(
            title="Choisir le fichier ADIF",
            filetypes=[("ADIF", "*.adi *.adif"), ("Tous les fichiers", "*.*")]
        )
        if p:
            self.source.set(p)
            if not self.destination.get():
                self.destination.set(str(Path(p).with_suffix(".log")))
            self.status.set(f"Fichier sélectionné : {Path(p).name}")

    def choose_destination(self):
        p = filedialog.asksaveasfilename(
            title="Enregistrer le Cabrillo",
            defaultextension=".log",
            filetypes=[("Cabrillo", "*.log *.cbr"), ("Tous les fichiers", "*.*")]
        )
        if p:
            self.destination.set(p)

    def convert(self):
        if not self.source.get():
            messagebox.showwarning("ADIF manquant", "Choisis d'abord le fichier ADI/ADIF.")
            return
        if not self.callsign.get().strip():
            messagebox.showwarning("Indicatif manquant", "Renseigne ton indicatif (champ \"Indicatif\").")
            return
        if not self.destination.get():
            self.choose_destination()
        if not self.destination.get():
            return

        header = {
            "contest": self.contest.get().strip().upper() or "CONTEST",
            "callsign": self.callsign.get().strip().upper(),
            "power": self.power.get().strip().upper() or "HIGH",
            "category_mode": self.category_mode.get().strip().upper() or "CW",
            "name": self.name.get().strip(),
            "address": self.address.get().strip(),
            "city": self.city.get().strip(),
            "country": self.country.get().strip(),
            "sent_exchange": self.sent_exchange.get().strip().upper(),
            "received_exchange": self.received_exchange.get().strip().upper(),
        }

        try:
            total, converted, skipped = convert_file(self.source.get(), self.destination.get(), header)
            self.status.set(f"{total} QSO lus — {converted} convertis — {skipped} ignorés.")
            data = Path(self.destination.get()).read_text(encoding="ascii", errors="replace")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", data[:12000])
            messagebox.showinfo(
                "Conversion terminée",
                f"Conversion terminée.\n\nQSO lus : {total}\n"
                f"QSO Cabrillo : {converted}\nQSO ignorés : {skipped}\n\n"
                f"Fichier :\n{self.destination.get()}"
            )
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

