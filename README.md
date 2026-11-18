# Android ADB Admin 2.3

## Changements v2.3

- Connexion ADB Wi-Fi : conservation du correctif de parsing validé en v2.2.
- Paiement opérateur : le profil restaure `com.xiaomi.payment` et les permissions/AppOps Play Store utilisées lors du dépannage précédent (`READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `READ_PHONE_STATE`). Chaque étape est vérifiée et les refus Android sont affichés sans faux succès.
- Launcher : l’option de recherche d’écran d’accueil est désormais une seule entrée dynamique `ACTIVÉE` / `DÉSACTIVÉE` / `NON DÉTECTÉE`, relue directement depuis Android.
- HyperOS : le programme ne prétend plus contrôler le geste exact si le launcher ne publie pas un réglage ADB sûr. `QSB_SCROLL_ENTRANCE_STATUS` est utilisé uniquement lorsqu’il est réellement exposé et vérifiable.
- Applications masquées : la restauration ne dépend plus uniquement de l’historique du programme. Le gestionnaire tente aussi de découvrir les activités `MAIN/LAUNCHER` désactivées et les applications entièrement désactivées, ce qui couvre les masquages effectués avant l’installation d’Android ADB Admin lorsque la version Android expose ces informations.


**Android ADB Admin** est un outil terminal Python pour administrer un appareil Android par **ADB**, avec un fonctionnement pensé en priorité pour **ADB Wi‑Fi**, Linux et Termux.

**Android ADB Admin** is a Python terminal tool for administering an Android device through **ADB**, designed primarily for **ADB over Wi‑Fi**, Linux and Termux.

> Utilise cet outil uniquement sur un téléphone que tu possèdes ou que tu es autorisé à administrer. Les fonctions de désactivation, désinstallation, suppression de journaux et modification de composants système peuvent avoir des conséquences importantes.
>
> Use this tool only on a phone you own or are authorized to administer. Disabling, uninstalling, deleting logs, or changing system components can have significant consequences.

---

# Français

## 1. Objectif

Android ADB Admin regroupe dans une seule interface terminal les opérations ADB courantes et plusieurs fonctions d'administration avancées : connexion ADB Wi‑Fi, applications, permissions/AppOps, fichiers, ports, diagnostics, contacts, SMS, journal d'appels, enregistrements `.ogg`, Launcher/HyperOS et exports d'urgence.

L'interface est volontairement compacte afin de rester lisible dans **Termux**. Le bandeau principal indique uniquement l'état d'ADB Wi‑Fi :

```text
====================================================
                 ANDROID ADB ADMIN 2.3
● ADB ACTIF — 192.168.x.x
====================================================
```

Sans connexion Wi‑Fi :

```text
● ADB OFF
```

L'USB reste disponible comme solution de configuration ou de dépannage, mais n'encombre pas l'affichage principal.

## 2. Installation

### Installation automatique recommandée

Le projet fournit `install.sh`. Il détecte son propre dossier, installe les dépendances système nécessaires, crée `.lib_venv` puis génère le lanceur local `admin.py`. Aucun chemin utilisateur n’est codé en dur.

```bash
chmod +x install.sh
./install.sh
python admin.py
```

Le fichier `admin.py` et le dossier `.lib_venv/` sont générés localement et ne sont pas destinés au dépôt Git.


### Linux Debian / Ubuntu / Mint / Kali

```bash
sudo apt update
sudo apt install adb python3 python3-pip
python3 -m pip install -r requirements.txt
python3 admin-adb.py
```

Pour le miroir d'écran :

```bash
sudo apt install scrcpy
```

### Termux

Installe Termux depuis une source à jour, puis :

```bash
pkg update
pkg install python android-tools
pip install -r requirements.txt
python admin-adb.py
```

`scrcpy` est facultatif et sa disponibilité dépend de l'environnement Termux utilisé.

## 3. Première connexion ADB Wi‑Fi

Dans le menu principal :

```text
[2] Connecter appareil
```

Deux méthodes sont proposées :

```text
[1] Connexion ADB Wi-Fi
[2] Configuration / réparation via USB
```

L'adresse IP saisie lors de la connexion Wi‑Fi est mémorisée dans la configuration locale de l'outil.

Par défaut, le port ADB TCP est `5555` lorsqu'une configuration via USB est demandée.

## 4. Gestion des applications

La liste des applications affiche :

```text
N°   PACKAGE                       APPLICATION           NIVEAU       UTILITE
```

Exemple :

```text
1    com.google.android.apps.docs  Google Drive          OK           Stockage Google Drive
2    com.android.systemui          Interface système     DECONSEILLE  Interface Android
```

### Identification des applications

Android ADB Admin utilise plusieurs sources :

1. dictionnaire interne pour Android, Google, Xiaomi/HyperOS et applications connues ;
2. informations exposées directement par Android ;
3. cache local ;
4. recherche Google Play pour un package inconnu sélectionné ;
5. recherche F-Droid lorsqu'elle est disponible ;
6. si l'identification reste incertaine : **À VÉRIFIER**.

L'outil ne doit pas inventer la fonction d'un package qu'il ne connaît pas.

### Niveaux de risque

**OK** : l'action demandée présente normalement peu de risques pour le fonctionnement du système.

**À VÉRIFIER** : le package est inconnu, préinstallé ou peut être lié à une fonction Android/HyperOS. Une explication est affichée avant l'action.

**DÉCONSEILLÉ** : composant critique. Le programme explique les conséquences possibles et demande une confirmation renforcée.

Le niveau dépend également de **l'action**. Inspecter un package peut être `OK` alors que le désinstaller peut être `DÉCONSEILLÉ`.

## 5. Démarrer une application

L'option de lancement affiche uniquement les noms utiles :

```text
[1] ChatGPT
[2] Google Drive
[3] Telegram
[4] Termux
```

Le package et l'Activity restent gérés en arrière-plan.

## 6. Gestionnaire de fichiers

Les transferts sont bidirectionnels :

- téléphone → ordinateur/Termux avec `adb pull` ;
- ordinateur/Termux → téléphone avec `adb push`.

Le navigateur Android reste dans le stockage partagé, principalement :

```text
/sdcard/
```

Il permet de naviguer par numéro et de créer un dossier directement :

```text
[M] Créer un dossier ici
```

La création utilise `mkdir -p` dans les emplacements où l'identité ADB possède les permissions nécessaires.

La racine Android `/` n'est pas proposée comme destination normale d'écriture.

## 7. Export des contacts

L'option **Exporter contacts JSON** tente de lire les providers Contacts accessibles à ADB et produit un fichier structuré :

```text
contacts_YYYY-MM-DD_HH-MM-SS.json
```

Structure générale :

```json
{
  "metadata": {
    "exported_at": "...",
    "count": 123,
    "format": "Android ADB Admin contacts dump"
  },
  "contacts": []
}
```

Les numéros et e-mails sont conservés sous forme structurée lorsqu'ils sont accessibles.

Sur certaines versions Android/HyperOS, l'identité `shell` d'ADB n'a pas le droit de lire les Contacts. Dans ce cas, l'outil signale l'échec au lieu de créer un faux export vide.

## 8. Dump SMS / Call

Le module est accessible dans :

```text
Sécurité / gestion Android
→ Android Manager
→ Dump SMS / Call
```

### SMS d'un contact

L'outil :

1. lit les SMS accessibles ;
2. lit les contacts accessibles ;
3. normalise les numéros ;
4. associe autant que possible numéro ↔ contact ;
5. affiche une liste numérotée ;
6. exporte uniquement la conversation sélectionnée en HTML.

Nom typique :

```text
SMS_Jean-Dupont_336xxxxxxxx_2026-09-01_01-30-00.html
```

### Appels d'un contact

Les journaux sont exportés en JSON. Les enregistrements sont cherchés par défaut dans :

```text
/sdcard/Recordings/
```

Formats audio recherchés :

```text
.ogg
.oga
```

L'association appel ↔ enregistrement est prudente : numéro/nom dans le fichier lorsqu'il est disponible, puis comparaison temporelle. Si plusieurs fichiers sont trop proches, l'outil marque l'association comme ambiguë au lieu de choisir arbitrairement.

L'export est regroupé dans une archive `.tar.gz` contenant notamment :

```text
CALL_Contact_Numero_Date/
├── call_logs.json
├── CALL_Contact_Numero_DateHeure.ogg
└── ...
```

## 9. Mode Urgence

Le menu Dump contient :

```text
[1] Exporter tout
[2] Exporter puis supprimer tout
[3] Supprimer tout sans export
```

### Exporter tout

L'outil génère un dossier autonome :

```text
Emergency_Dump_YYYY-MM-DD_HH-MM-SS/
├── index.html
├── database/
│   ├── emergency.db
│   ├── contacts.json
│   ├── sms.json
│   ├── calls.json
│   └── manifest.json
└── calls/
    └── recordings/
        ├── ....ogg
        └── ...
```

`index.html` fonctionne localement et permet de rechercher les SMS, appels et contacts. Les fichiers audio restent de vrais fichiers `.ogg` accessibles séparément.

`emergency.db` est une base SQLite pour une exploitation structurée des données.

Une fois construit, le dossier est compressé en :

```text
Emergency_Dump_YYYY-MM-DD_HH-MM-SS.tar.gz
```

### Exporter puis supprimer

L'ordre est volontairement strict :

1. collecte ;
2. création JSON/SQLite/HTML ;
3. copie des `.ogg` ;
4. création du `.tar.gz` ;
5. vérification du contenu de l'archive ;
6. copie de l'archive vers la destination demandée ;
7. seulement après succès : proposition de suppression.

Si l'archive est invalide ou ne peut pas être livrée, aucune suppression automatique n'est lancée.

### Suppression totale

La suppression exige la saisie :

```text
SUPPRIMER TOUT
```

La possibilité réelle de supprimer SMS et call logs dépend des permissions que la ROM accorde à l'identité ADB `shell`.

## 10. Launcher / écran d'accueil HyperOS

Le module Launcher peut :

- détecter l'Activity HOME ;
- afficher des informations sur `com.miui.home` ;
- masquer l'icône Launcher d'une application en désactivant uniquement son composant `MAIN/LAUNCHER` ;
- mémoriser le composant afin de pouvoir restaurer l'icône ;
- lire et tester certains paramètres de recherche du Launcher ;
- vérifier le résultat après modification.

Une commande acceptée par ADB n'est **pas** considérée automatiquement comme un succès. L'outil relit l'état après l'action.

La barre de recherche Google dépend fortement de la version exacte du Launcher HyperOS. Le programme affiche `NON SUPPORTÉ / non vérifiable` lorsqu'il ne peut pas confirmer le changement.

## 11. Permissions, AppOps, ports et réseau

Le module avancé conserve les outils de diagnostic ADB : permissions déclarées/accordées, AppOps, connexions, ports, UID/packages et commandes de diagnostic réseau disponibles sur la ROM.

Certaines informations `/proc`, sockets ou règles réseau sont volontairement limitées par Android lorsqu'ADB n'a pas les droits root.

## 12. Fichiers de configuration

Les préférences sont stockées sous :

```text
~/.config/android-adb-admin/
```

On y trouve notamment l'adresse ADB Wi‑Fi mémorisée, le chemin `Recordings`, le cache d'identification d'applications et les composants Launcher masqués.

Ne publie pas ce dossier de configuration dans un dépôt GitHub personnel s'il contient des informations sur tes appareils.

## 13. Tests effectués avant cette livraison

Cette version a été vérifiée par compilation Python et par simulations locales portant sur :

- parsing de sorties `content query` SMS ;
- normalisation des numéros français/internationaux ;
- association numéro ↔ contact ;
- association temporelle call log ↔ `.ogg` ;
- classification `OK / À VÉRIFIER / DÉCONSEILLÉ` ;
- génération de l'interface HTML du dump d'urgence.

Ces simulations ne remplacent pas un vrai téléphone HyperOS. Xiaomi peut modifier les permissions, providers et comportements du Launcher entre deux builds.

## 14. Dépannage

Vérifier ADB :

```bash
adb version
adb devices
```

Tester une connexion Wi‑Fi :

```bash
adb connect IP_DU_TELEPHONE:5555
```

Vérifier le dossier d'enregistrements :

```bash
adb shell ls -la /sdcard/Recordings/
```

Vérifier le Launcher :

```bash
adb shell cmd package resolve-activity --brief \
  -a android.intent.action.MAIN \
  -c android.intent.category.HOME
```

Vérifier la syntaxe du programme :

```bash
python -m py_compile admin-adb.py
```

## 15. Publication GitHub

Avant publication :

- ne mets aucun dump de SMS, contact, appel ou audio dans le dépôt ;
- ne mets aucun log contenant une adresse IP privée/publique que tu ne souhaites pas partager ;
- ne publie aucune clé ADB privée ;
- ajoute une licence adaptée à ton projet si tu veux autoriser explicitement la réutilisation du code ;
- teste les fonctions destructives sur un appareil de test avant de les présenter comme compatibles avec une nouvelle ROM.

---

# English

## 1. Purpose

Android ADB Admin combines common ADB operations and advanced Android administration in a compact terminal interface optimized for **ADB over Wi‑Fi**, Linux and Termux.

It includes application management, risk assessment, file transfers, permissions/AppOps, diagnostics, contacts, SMS, call logs, `.ogg` call recordings, HyperOS Launcher tools and emergency exports.

## 2. Installation

### Debian / Ubuntu / Mint / Kali

```bash
sudo apt update
sudo apt install adb python3 python3-pip
python3 -m pip install -r requirements.txt
python3 admin-adb.py
```

Optional screen mirroring:

```bash
sudo apt install scrcpy
```

### Termux

```bash
pkg update
pkg install python android-tools
pip install -r requirements.txt
python admin-adb.py
```

## 3. ADB over Wi‑Fi

The main status banner focuses on the Wi‑Fi connection:

```text
● ADB ACTIF — 192.168.x.x
```

or:

```text
● ADB OFF
```

USB remains available as a setup/recovery method but is not shown as the normal operating mode.

## 4. Application identification and safety levels

Application entries can contain the package ID, readable title, purpose/category and a risk level.

The identification engine uses an internal catalog, Android metadata, a local cache and optional best-effort lookups for unknown packages on Google Play or F-Droid.

Risk levels are action-dependent:

- **OK**: low expected system impact;
- **CHECK / À VÉRIFIER**: unknown/preinstalled/dependency-sensitive package;
- **NOT RECOMMENDED / DÉCONSEILLÉ**: critical Android/HyperOS component.

Critical actions require stronger confirmation.

## 5. File manager

The file manager supports:

- phone → computer/Termux (`adb pull`);
- computer/Termux → phone (`adb push`);
- browsing `/sdcard`;
- creating folders with `mkdir -p`;
- selecting a destination directory without typing the full Android path.

The Android filesystem root is not offered as a normal writable destination.

## 6. Contacts JSON export

Contacts are exported as structured JSON when Android allows ADB shell access to the Contacts provider.

If access is denied, Android ADB Admin reports the failure instead of pretending that an empty dump is valid.

## 7. SMS / Call dump

SMS export is contact-oriented and generates readable HTML. Phone-number normalization is used to match locally formatted numbers to international contact numbers.

Call logs are stored as JSON. Call recordings are searched under:

```text
/sdcard/Recordings/
```

The expected audio format is `.ogg`/`.oga`.

Call-to-recording matching uses filenames when possible and timestamp proximity otherwise. Ambiguous matches are left unassigned instead of being guessed.

## 8. Emergency dump

Emergency export creates a self-contained dataset with:

- `index.html` searchable offline interface;
- JSON data files;
- SQLite `emergency.db`;
- original `.ogg` recording copies;
- `manifest.json` export metadata.

The directory is validated and compressed to `.tar.gz` before delivery.

For **export then delete**, deletion is not started unless the archive was successfully built, validated and delivered.

## 9. HyperOS Launcher

The Launcher module detects the HOME activity and can hide/restore app launcher components. Hidden components are remembered locally so they can be restored later.

Search-related HyperOS settings are treated as device-dependent. ADB command acceptance alone is not considered proof of success: the program reads the setting back and reports unsupported/unverifiable states when necessary.

## 10. Android limitations

Modern Android versions can deny ADB shell access to Contacts, SMS, call logs, `/proc`, application internals or firewall controls. Root access changes what is technically possible, but Android ADB Admin does not fake root-only capabilities on a non-rooted device.

Xiaomi/HyperOS launcher behavior is also build-dependent. Always verify destructive operations on the exact ROM/build you intend to support.

## 11. Privacy

Emergency dumps, contact exports, SMS exports and call recordings contain highly private information. Keep them outside your Git repository and protect them appropriately.

Never publish ADB private keys, personal configuration files or real user dumps.

## 12. Development / validation

Check Python syntax with:

```bash
python -m py_compile admin-adb.py
```

The delivered build was additionally tested with simulated ADB output for SMS parsing, phone normalization, contact matching, call-recording matching, risk classification and emergency HTML generation.

## 13. Contributing / GitHub

When publishing or accepting contributions:

- document the Android and HyperOS build used for tests;
- do not mark a command as supported unless its result can be verified;
- never add real private dumps as test fixtures;
- keep destructive actions behind explicit confirmation;
- prefer graceful `unsupported` results over unsafe assumptions.

---

## Project files

```text
Android-ADB-Admin-v2.0/
├── admin-adb.py
├── requirements.txt
└── README.md
```

## License

No software license is imposed by this README. If you publish the project publicly, add the license you actually want to use (MIT, GPL-3.0, Apache-2.0, etc.) and make sure any third-party code you include is compatible with it.

---

## v2.1 — Correctif ADB Wi‑Fi / Wi‑Fi ADB fix

**FR :** correction du bandeau ADB Wi‑Fi. Le programme accepte maintenant les différentes formes de retour de la liste des appareils ADB (chaîne, tuple/liste ou dictionnaire) et ne plante plus avec `ValueError: too many values to unpack`. Correction également de l'import `pathlib.Path` utilisé par la configuration de langue.

**EN:** fixed the Wi‑Fi ADB status banner. The program now accepts different device-list return shapes (string, tuple/list, or dictionary) and no longer crashes with `ValueError: too many values to unpack`. Also fixed the missing `pathlib.Path` import used by language configuration.

Installation / setup:

```bash
chmod +x install.sh
./install.sh
```

Then launch / puis lancer:

```bash
python admin.py
```
