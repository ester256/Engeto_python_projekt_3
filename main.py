# Elections_scrapper.py: třetí projekt do Engeto Online Python Akademie

# author: Ester Bubíková
# email: ester.bubikova@gmail.com
# discord: Ester #st8115

import requests
import csv
import click
import time
from bs4 import BeautifulSoup as bs


# FUNKCE

## Stránka okresu


def nacti_stranku_okresu(url: str) -> bs | None:
    """
    Načte HTML stránku okresu z volby.cz.
    Vrací BeautifulSoup nebo None.
    """
    try:
        with requests.Session() as session:
            odp = session.get(url, timeout=10)

    except requests.RequestException:
        raise click.ClickException(
            f"Nepovedlo se připojit k {url}. Zkontroluj své připojení."
        )

    if not (odp.status_code >= 200 and odp.status_code < 300):
        raise click.ClickException(
            f"Při pokusu o načtení stránky {url} se vyskytla chyba {odp.status_code}."
        )

    return bs(odp.text, features="html.parser")


def extrahuj_jmena_obci(stranka_okresu: bs) -> list[str]:
    """
    Získá názvy obcí z HTML stránky okresu.
    """

    vsechny_td = stranka_okresu.find_all("td", {"class": "overflow_name"})
    return [td.get_text(strip=True) for td in vsechny_td]


def extrahuj_kody_obci(stranka_okresu: bs) -> list[str]:
    """
    Získá kódy obcí z HTML stránky okresu.
    """

    vsechny_td = stranka_okresu.find_all("td", {"class": "cislo"})
    vsechny_a = [td.find("a") for td in vsechny_td]
    return [a.get_text(strip=True) for a in vsechny_a]


def extrahuj_odkazy_obci(stranka_okresu: bs) -> list[str]:
    """
    Získá relativní odkazy na stránky obcí.
    """

    vsechny_td = stranka_okresu.find_all("td", {"class": "cislo"})
    vsechny_a = [td.find("a") for td in vsechny_td]
    return [a["href"] for a in vsechny_a]


def poskladej_slovnik_obci(kody_obci: list[str], jmena_obci: list[str]) -> list[dict]:
    """
    Spojí kódy a jména obcí do seznamu slovníků.
    """

    return [{"kod": kod, "obec": jmeno} for kod, jmeno in zip(kody_obci, jmena_obci)]


def preved_odkazy(odkazy: list[str]) -> list[str]:
    """
    Převede relativní odkazy obcí na absolutní URL.
    """

    return [("https://www.volby.cz/pls/ps2017nss/" + odkaz) for odkaz in odkazy]


## Stránky obcí


def nacti_stranky_obci(absolutni_odkazy: list[str]) -> list[requests.Response]:
    """
    Stáhne HTML stránky obcí, vrací jen odpovědi s kódem 2xx.
    """

    odpoved_serveru = []

    with requests.Session() as session:
        for odkaz in absolutni_odkazy:
            odp = session.get(odkaz, timeout=10)
            if odp.status_code >= 200 and odp.status_code < 300:
                odpoved_serveru.append(odp)
            else:
                print(f"Nepovedlo se načíst data pro odkaz: {odkaz}")

            time.sleep(0.5)

    return odpoved_serveru


def uvar_polevky_obci(odpovedi_serveru: list[requests.Response]) -> list[bs]:
    """
    Převede HTML odpovědi na objekty BeautifulSoup.
    """

    return [bs(odpoved.text, features="html.parser") for odpoved in odpovedi_serveru]


def extrahuj_volice(data_obci: list[bs], obce: list[dict]) -> list[dict]:
    """
    Přidá k obcím počty voličů.
    """

    for i in range(len(data_obci)):
        obce[i]["volici"] = (
            data_obci[i]
            .find("td", {"class": "cislo", "headers": "sa2"})
            .get_text(strip=True)
            .replace("\xa0", "")
        )
    return obce


def extrahuj_obalky(data_obci: list[bs], obce: list[dict]) -> list[dict]:
    """
    Přidá k obcím počty obálek.
    """

    for i in range(len(data_obci)):
        obce[i]["obalky"] = (
            data_obci[i]
            .find("td", {"class": "cislo", "headers": "sa3"})
            .get_text(strip=True)
            .replace("\xa0", "")
        )
    return obce


def extrahuj_platne_hlasy(data_obci: list[bs], obce: list[dict]) -> list[dict]:
    """
    Přidá k obcím počty platných hlasů.
    """

    for i in range(len(data_obci)):
        obce[i]["platne_hlasy"] = (
            data_obci[i]
            .find("td", {"class": "cislo", "headers": "sa6"})
            .get_text(strip=True)
            .replace("\xa0", "")
        )
    return obce


def extrahuj_hlasy_stran(data_obci: list[bs], obce: list[dict]) -> list[dict]:
    """
    Přidá k obcím hlasy jednotlivých stran.
    """

    for i in range(len(data_obci)):
        strany_col_1 = data_obci[i].find_all(
            "td", {"class": "overflow_name", "headers": "t1sa1 t1sb2"}
        )
        strany_col_2 = data_obci[i].find_all(
            "td", {"class": "overflow_name", "headers": "t2sa1 t2sb2"}
        )
        hlasy_col_1 = data_obci[i].find_all(
            "td", {"class": "cislo", "headers": "t1sa2 t1sb3"}
        )
        hlasy_col_2 = data_obci[i].find_all(
            "td", {"class": "cislo", "headers": "t2sa2 t2sb3"}
        )
        strany = strany_col_1 + strany_col_2
        hlasy = hlasy_col_1 + hlasy_col_2

        for strana, hlas in zip(strany, hlasy):
            obce[i][strana.get_text(strip=True)] = hlas.get_text(strip=True).replace(
                "\xa0", ""
            )

    return obce


def extrahuj_data_obci(data_obci: list[bs], obce: list[dict]) -> list[dict]:
    """
    Spojí extrahovaná data všech kategorií do jednoho seznamu obcí.
    """

    volici = extrahuj_volice(data_obci, obce)
    obalky = extrahuj_obalky(data_obci, obce)
    platne_hlasy = extrahuj_platne_hlasy(data_obci, obce)
    hlasy_stran = extrahuj_hlasy_stran(data_obci, obce)
    return [
        {**volic, **obalka, **platny_hlas, **hlas_strany}
        for volic, obalka, platny_hlas, hlas_strany in zip(
            volici, obalky, platne_hlasy, hlasy_stran
        )
    ]


## CSV


def uloz_data_do_CSV(obce: list[dict], nazev_CSV: str) -> None:
    """
    Uloží volební data obcí do CSV souboru.
    """

    nazev_CSV = zkontroluj_nazev_CSV(nazev_CSV)

    with open(nazev_CSV, mode="w", encoding="windows-1250", newline="") as soubor:
        writer = csv.DictWriter(soubor, fieldnames=(obce[0].keys()))
        writer.writeheader()
        for obec in obce:
            writer.writerow(obec)
    print(f"Soubor {nazev_CSV} byl úspěšně vytvořen.")


def zkontroluj_nazev_CSV(nazev_CSV: str) -> str:
    """
    Ověří příponu .csv, případně ji doplní.
    """

    if not nazev_CSV.lower().endswith(".csv"):
        nazev_CSV += ".csv"
    return nazev_CSV


@click.command(
    help="""
Scraper volebních výsledků parlamentních voleb 2017

URL – musí být odkaz na stránku z volby.cz pro volby do poslanecké sněmovny parlamentu z roku 2017 na úrovni územních celků: 
https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ.

Vyber si územní celek, který tě zajímá, a rozklikni X pod nadpisem Výběr obce. Odkaz na tuto stránku vlož v uvozovkách jako první argument.

NAZEV_SOUBORU – název výsledného CSV souboru. Nepoužívej diaktritiku ani mezery. 

"""
)
@click.argument("url")
@click.argument("nazev_souboru")
def main(url, nazev_souboru):
    if "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=" not in url:
        raise click.BadParameter(
            "Nesprávný odkaz.\n Prosím zadej odkaz pro výsledky voleb do Poslanecké sněmovny z roku 2017 z volby.cz (viz --help)."
        )
    else:
        stranka_okresu = nacti_stranku_okresu(url)
        relativni_odkazy = extrahuj_odkazy_obci(stranka_okresu)
        kody_obci = extrahuj_kody_obci(stranka_okresu)
        jmena_obci = extrahuj_jmena_obci(stranka_okresu)
        absolutni_odkazy = preved_odkazy(relativni_odkazy)
        obce = poskladej_slovnik_obci(kody_obci, jmena_obci)
        stranky_obci = nacti_stranky_obci(absolutni_odkazy)
        data_obci = uvar_polevky_obci(stranky_obci)
        obce = extrahuj_data_obci(data_obci, obce)
        uloz_data_do_CSV(obce, nazev_souboru)


if __name__ == "__main__":
    main()
