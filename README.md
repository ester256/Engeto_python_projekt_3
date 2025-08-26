# Projekt Elections Scrapper (volby.cz)

Tento projekt slouží k automatickému stažení výsledků voleb do poslanecké sněmovny z roku 2017 pro jednotlivé územní celky.
Data jsou následně uložena do souboru CSV.

---

## Instalace

1. Naklonujte nebo stáhněte tento repozitář.
2. Ujistěte se, že máte nainstalovaný **Python 3.10+**.
3. Nainstalujte potřebné knihovny:

```
pip install -r requirements.txt
```

---

## Použití
Skript se spouští z příkazové řádky pomocí knihovny click.
Vyžaduje dva povinné argumenty:

**url** – adresa stránky odkazující na výsledky územního celku:
1. otevřete stránku https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ
2. rozklikněte X pod nadpisem Výběr obce pro územní celek, který vás zajímá

**nazev_csv** – název výstupního souboru bez diakritiky či mezer

Příklad spuštění:
```
python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8103" "Karvina.csv"
```

---

## Výstup
Po spuštění programu se vytvoří CSV soubor s daty pro vybrané území.
Ukázka struktury výstupu pro okres Karviná:

```
kod,obec,volici,obalky,platne_hlasy,Občanská demokratická strana,...
598925,Albrechtice,3173,1957,1944,109,...
599051,Bohumín,17613,9040,8973,579,...
598933,Český Těšín,19635,10429,10361,698,..
```
