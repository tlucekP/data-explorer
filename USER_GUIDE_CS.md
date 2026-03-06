# Lokální Data Explorer – uživatelský manuál

Lokální Data Explorer je nástroj pro **bezpečnou analýzu datových souborů a jejich použití s AI**.

Aplikace analyzuje data **lokálně** a umožňuje jejich odeslání do AI **pouze po explicitním rozhodnutí uživatele**.

Podporované typy souborů:

* CSV
* TXT
* MD

---

# 1. Hlavní princip aplikace

Aplikace funguje ve třech krocích:

1️⃣ **Offline analýza dat**

* profiling datasetu
* statistiky
* kontrola kvality dat

2️⃣ **Offline detekce osobních údajů (PII)**

* e-mail
* telefon
* rodné číslo
* bankovní účet / IBAN
* adresa
* jméno

3️⃣ **Bezpečné použití AI**

* pouze anonymizovaná data
* pouze po kliknutí uživatele

---

# 2. Bezpečnostní model

Aplikace používá několik bezpečnostních pravidel:

### Žádné automatické volání AI

AI se nikdy nevolá při:

* načtení aplikace
* změně souboru
* změně složky
* změně filtrů

AI se volá **pouze tlačítkem**:

```
Odeslat do AI
```

---

### Offline zpracování dat

Tyto operace probíhají **lokálně**:

* profiling datasetu
* PII detekce
* anonymizace

Data opustí počítač pouze při volání AI.

---

### Originální dataset s PII nelze odeslat

Pokud aplikace detekuje osobní údaje:

```
originální dataset nelze použít pro AI
```

Nejdříve je nutné vytvořit anonymizovanou verzi.

---

# 3. Spuštění aplikace

### Doporučený způsob

Spusťte:

```
start_data_explorer.bat
```

Aplikace se otevře v prohlížeči:

```
http://localhost:8501
```

---

### Ruční spuštění

```
pip install -r requirements.txt
streamlit run app.py
```

---

# 4. Výběr souborů

1️⃣ Vyberte složku se soubory
2️⃣ aplikace provede sken složky
3️⃣ soubory se zobrazí v levém panelu

Podporované filtry:

* název souboru
* typ souboru
* velikost
* datum změny

---

# 5. Offline profiling

Po kliknutí na soubor aplikace provede analýzu.

Pro CSV:

* počet řádků
* počet sloupců
* schéma
* chybějící hodnoty
* statistiky
* duplicity
* top hodnoty

Pro text:

* počet znaků
* počet řádků
* počet slov
* klíčová slova

Profiling probíhá **lokálně**.

---

# 6. PII report

Aplikace automaticky hledá osobní údaje.

Detekované typy:

```
EMAIL
PHONE
DOB
RC
BANK
NAME
ADDRESS
```

Výsledek se zobrazí v tabulce:

* typ PII
* řádek
* sloupec
* maskovaná hodnota
* detekční pravidlo
* confidence

---

# 7. Demaskování hodnot

Kliknutím na:

```
Zobrazit
```

je možné zobrazit skutečnou hodnotu.

Bezpečnostní pravidla:

* zobrazí se pouze jeden záznam
* automaticky se skryje po 30 sekundách
* nezapisuje se do logu

---

# 8. Označení false positive

Pokud je detekce chybná:

```
Označit za bezpečné
```

Nález se odstraní z reportu.

Platnost:

* pouze pro aktuální soubor
* pouze pro aktuální privacy mode
* resetuje se při změně souboru

---

# 9. Anonymizace dat

Tlačítko:

```
Anonymizovat pro AI
```

nahradí osobní údaje tokeny.

Například:

```
EMAIL → EMAIL_1
PHONE → PHONE_1
NAME → NAME_1
```

Vlastnosti anonymizace:

* konzistentní tokeny
* stejná hodnota → stejný token
* mapování je per dataset

---

# 10. AI Chat

AI Chat umožňuje analyzovat dataset pomocí modelu Mistral.

AI dostane pouze **metadata datasetu**.

Možnosti kontextu:

```
schema
schema+stats
schema+stats+sample
```

---

# 11. Sample datasetu

Sample obsahuje omezený počet řádků:

Strict:
100 řádků

Balanced:
200 řádků

Relaxed:
300 řádků

V režimu **Strict** se navíc odstraňují ID-like sloupce.

---

# 12. Limit velikosti AI kontextu

Maximální velikost payloadu:

```
200 KB
```

Pokud je kontext větší:

```
sample datasetu se odstraní
```

AI dostane pouze schema a statistiky.

---

# 13. Privacy mode

### Strict

* nejvyšší citlivost
* sample max 100
* odstranění ID-like sloupců

### Balanced

* střední citlivost
* sample max 200

### Relaxed

* nejnižší citlivost
* sample max 300
* zvýšené riziko přehlédnutí PII

---

# 14. Logování

Logují se pouze metadata:

* výběr souboru
* dokončení profilování
* PII detekce
* anonymizace
* AI request

Neloguje se:

* obsah datasetu
* prompt
* demaskované hodnoty

---

# 15. Doporučené použití

Pro reálná data:

```
Strict mode
```

Do AI posílejte co nejmenší kontext.

Například:

```
schema
schema+stats
```

---

# 16. Typické chyby

### PII detected

Dataset obsahuje osobní údaje.

Řešení:

```
Anonymizovat pro AI
```

---

### Missing MISTRAL_API_KEY

Není nastaven API klíč.

Řešení:

```
.env → MISTRAL_API_KEY
```

---

### No module named mistralai

Nainstalujte závislosti:

```
pip install -r requirements.txt
```
