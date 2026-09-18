ADIF → Cabrillo (F4GOP)
Petit outil avec interface graphique (Tkinter) pour convertir un journal de trafic ADIF (`.adi` / `.adif`) en fichier Cabrillo prêt à être soumis pour un concours radioamateur.
Fonctionnalités
Lecture des enregistrements ADIF standards (délimités par `<EOR>`)
Détection automatique du mode Cabrillo (`CW`, `PH`, `RY`) à partir du champ `MODE`/`SUBMODE`
Calcul de la fréquence en kHz à partir du champ `FREQ` ou, à défaut, de la bande (`BAND`)
Champs d'échange (envoyé/reçu) personnalisables, car le format d'échange dépend du concours et n'est pas toujours présent dans l'ADIF
Aperçu du fichier Cabrillo généré directement dans l'interface
Tri automatique des QSO par date/heure

Utilisation
Lance `ADIF_to_Cabrillo_F4GOP.py` (nécessite Python avec Tkinter, inclus par défaut sous Windows).
Sélectionne ton fichier ADIF.
Renseigne les informations du concours (indicatif, puissance, catégorie, échange envoyé/reçu, etc.).
Choisis l'emplacement du fichier Cabrillo de sortie.
Clique sur CONVERTIR ADIF → CABRILLO.

Compiler en exécutable Windows (.exe)
Un script `build_exe.bat` est fourni pour générer un exécutable autonome via PyInstaller :
Place `build_exe.bat` dans le même dossier que `ADIF_to_Cabrillo_F4GOP.py`.
Double-clique sur `build_exe.bat`.
Récupère `ADIF_to_Cabrillo_F4GOP.exe` dans le dossier `dist/` généré.

Notes
Les champs d'échange (RST, échange concours) ne sont jamais inventés : s'ils sont absents de l'ADIF, ils restent vides sauf si tu les renseignes manuellement dans l'interface.
Les enregistrements ADIF sans `CALL` ou `QSO_DATE` valides sont ignorés (comptés comme "ignorés" dans le résumé de conversion).

Auteur
Denis — F4GOP (IN98QR, Flers, Normandie, France)
