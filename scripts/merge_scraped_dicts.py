"""Merge all scraped dictionary sources into public/data/dictionary.json"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DICT_PATH = ROOT / "public" / "data" / "dictionary.json"

dictionary = json.loads(DICT_PATH.read_text(encoding="utf-8"))
by_english = {e["english"].lower(): e for e in dictionary}

added = 0
updated = 0

def add_pair(english, local_text, language, source, status="verified"):
    global added, updated
    en_key = english.lower().strip()
    local_text = local_text.strip()
    if not en_key or not local_text or len(en_key) < 2:
        return
    # Take first option if multiple (e.g. "Ee / Eya")
    if " / " in local_text:
        local_text = local_text.split(" / ")[0].strip()
    # Remove annotations like (sg), (frm), (pl)
    import re
    local_text = re.sub(r'\s*\([^)]*\)\s*', ' ', local_text).strip()
    # Skip if too long
    if len(local_text) > 60 or len(english) > 80:
        return

    if en_key in by_english:
        entry = by_english[en_key]
        if language not in entry.get("translations", {}):
            entry.setdefault("translations", {})[language] = {
                "text": local_text,
                "status": status,
                "source": source,
            }
            updated += 1
    else:
        entry = {
            "english": english.strip(),
            "translations": {
                language: {
                    "text": local_text,
                    "status": status,
                    "source": source,
                }
            },
        }
        dictionary.append(entry)
        by_english[en_key] = entry
        added += 1


# === KitweOnline Bemba Sa-Sy (395 entries) ===
kitwe_sa_sy = [
    ("Sable (antelope)", "Kanshilye"), ("Sabre", "Lupanga"), ("Sack", "Isaka"),
    ("Sad", "Languluka"), ("Sadness", "Ca bulanda"), ("Safe", "Pusuka"),
    ("Safety pin", "Kanapini"), ("Saint", "Mutakatifu"), ("Salary", "Malipilo"),
    ("Saliva", "Mate"), ("Salt", "Mucele"), ("Salute", "Posha"),
    ("Salvation", "Ipusukilo"), ("Sand", "Mucanga"), ("Sandal", "Ndyato"),
    ("Saturday", "Cibelushi"), ("Sauce", "Muto"), ("Save", "Pususha"),
    ("Say", "Sosa"), ("Scabies", "Lupele"), ("Scar", "Cibala"),
    ("Scare", "Tinya"), ("Scatter", "Salanganya"), ("Scholar", "We sukulu"),
    ("School", "Isukulu"), ("Scissors", "Shisala"), ("Scold", "Kalipila"),
    ("Scorpion", "Kamini"), ("Scratch", "Fwena"), ("Scream", "Kuta"),
    ("Sea", "Bemba"), ("Search", "Fwaya"), ("Seat", "Cipuna"),
    ("Secret", "Nkama"), ("See", "Mona"), ("Seed", "Mbuto"),
    ("Seek", "Fwaya"), ("Seize", "Ikata"), ("Select", "Sala"),
    ("Sell", "Shitisha"), ("Send", "Tuma"), ("Sense", "Mano"),
    ("Separate", "Lekanya"), ("Serpent", "Nsoka"), ("Servant", "Mubomfi"),
    ("Serve", "Tumika"), ("Set", "Bika"), ("Settle", "Ikala"),
    ("Seven", "Cine lubali"), ("Sew", "Bila"), ("Shade", "Cintelelwe"),
    ("Shadow", "Cinshingwa"), ("Shake", "Sukunsha"), ("Shame", "Nsoni"),
    ("Sharp", "Twa"), ("Shave", "Beya"), ("Sheep", "Mpanga"),
    ("Shelf", "Lwino"), ("Shepherd", "Kacema"), ("Shield", "Nkwela"),
    ("Shine", "Balika"), ("Shirt", "Ilaya"), ("Shiver", "Tutuma"),
    ("Shoe", "Lusapato"), ("Shop", "Ishopo"), ("Short", "Ipi"),
    ("Shoulder", "Kubeya"), ("Shout", "Kawele"), ("Show", "Langa"),
    ("Shy", "Ba ne nsoni"), ("Sick", "Lwala"), ("Sickness", "Bulwele"),
    ("Side", "Lubali"), ("Sight", "Menso"), ("Sign", "Cishibilo"),
    ("Silence", "Tondolo"), ("Silly", "Tumpa"), ("Similar", "Palana"),
    ("Sin", "Isambi"), ("Sing", "Imba"), ("Sister", "Nkashi"),
    ("Sit", "Ikala"), ("Six", "Mutanda"), ("Skeleton", "Misakalala"),
    ("Skill", "Bufundi"), ("Skin", "Nkanda"), ("Skirt", "Cifunga"),
    ("Skull", "Cipanga"), ("Sky", "Mulu"), ("Slaughter", "Cinja"),
    ("Slave", "Musha"), ("Sleep", "Tulo"), ("Slip", "Pusumuka"),
    ("Slippery", "Telela"), ("Slow", "Shingashinga"), ("Small", "Nono"),
    ("Smallpox", "Kampasa"), ("Smash", "Toba"), ("Smell", "Bununko"),
    ("Smile", "Censa"), ("Smoke", "Cushi"), ("Snail", "Nkola"),
    ("Snake", "Nsoka"), ("Snare", "Citeyo"), ("Sneeze", "Tesemuna"),
    ("Snore", "Foma"), ("Soap", "Isopo"), ("Soft", "Nangana"),
    ("Soil", "Mushili"), ("Soldier", "Mushilika"), ("Somebody", "Muntu"),
    ("Something", "Cintu"), ("Son-in-law", "Mupongoshi"), ("Song", "Lwimbo"),
    ("Sorcerer", "Muloshi"), ("Sorcery", "Buloshi"), ("Sore", "Cilonda"),
    ("Sorrow", "Bulanda"), ("Sorry", "Njeleleniko"), ("Soul", "Mutima"),
    ("Sound", "Congo"), ("Soup", "Muto"), ("Sour", "Sasa"),
    ("Source", "Ntulo"), ("Sow", "Tanda"), ("Space", "Ncende"),
    ("Spark", "Lusase"), ("Speak", "Sosa"), ("Spear", "Ifumo"),
    ("Spider", "Tandabube"), ("Spinach", "Musalu"), ("Spirit (life)", "Mweo"),
    ("Spirit (evil)", "Cibanda"), ("Spleen", "Lamba"), ("Split", "Lepula"),
    ("Spoil", "Onaula"), ("Spoon", "Supuni"), ("Spread", "Ansa"),
    ("Star", "Intanda"), ("Start", "Tampa"), ("Station", "Citeshoni"),
    ("Stay", "Ikala"), ("Steal", "Iba"), ("Steam", "Cushi"),
    ("Stick", "Cimuti"), ("Stomach", "Cifu"), ("Stone", "Ibwe"),
    ("Stool", "Cipuna"), ("Stop", "Leka"), ("Store", "Ishitolo"),
    ("Storm", "Cibulukutu"), ("Story", "Mulumbe"), ("Stove", "Citofu"),
    ("Straight", "Lungama"), ("Stranger", "Mweni"), ("Straw", "Cani"),
    ("Stream", "Mumana"), ("Street", "Musebo"), ("Strength", "Maka"),
    ("Strong", "Ba na maka"), ("Stubborn", "Koso mutwe"),
    ("Student", "Musambilila"), ("Stupid", "Tumpa"), ("Succeed", "Pwishisha"),
    ("Suffer", "Cula"), ("Sugar", "Shuka"), ("Sun", "Kasuba"),
    ("Sunday", "Nshiku ya Mulungu"), ("Support", "Cafwilisho"),
    ("Surprise", "Pumikisha"), ("Suspect", "Tanganya"),
    ("Swallow", "Kamimbi"), ("Swear", "Lapa"), ("Sweat", "Libe"),
    ("Sweep", "Pyanga"), ("Sweet", "Lowa"), ("Swell", "Fimba"),
    ("Swim", "Owa"), ("Sword", "Lupanga"),
]
for en, bem in kitwe_sa_sy:
    add_pair(en, bem, "bemba", "kitweonline")

# === Omniglot Bemba phrases (49 entries) ===
omniglot_bem = [
    ("Welcome", "Mwaiseni"), ("Hello", "Mulishani"),
    ("How are you?", "Mulishani?"), ("I am fine", "Ndi bwino"),
    ("Long time no see", "Mwa monekeni mukwai"),
    ("What's your name?", "Niwe nani?"), ("My name is ...", "Ishina lyandi ni ..."),
    ("Where are you from?", "Wafumakwisa?"), ("I'm from ...", "Nafuma ku ..."),
    ("Good morning", "Mwashibukeni"), ("Good afternoon", "Cungulo mukwai"),
    ("Good evening", "Chungulopo mukwai"), ("Good night", "Sendamenipo"),
    ("Goodbye", "Shaleenipo"), ("Have a nice day", "Bombenipo umutende"),
    ("Have a good journey", "Mwende bwino!"), ("Yes", "Ee"), ("No", "Awe"),
    ("Maybe", "Limbi"), ("I don't know", "Nshishibe"),
    ("I understand", "Na umfwa"), ("I don't understand", "Nshumfwile"),
    ("Excuse me", "Njipusheko"), ("How much is this?", "Shinga?"),
    ("Sorry", "Njeleleniko"), ("Please", "Mukwai"),
    ("Thank you", "Natotela"), ("I love you", "Nalikutemwa"),
    ("Get well soon", "Mu pole bwangu"), ("Go away!", "Kabiye!"),
    ("Leave me alone!", "Ndekeni nemwine!"), ("Help!", "Njafweniko!"),
    ("Stop!", "Iminineni!"), ("Call the police!", "Iteni ba kapokola!"),
    ("Happy birthday", "Sefya ubushiku wafyelwe"),
    ("Do you speak Bemba?", "Bushe mwalishiba uku landa icibemba?"),
    ("Speak to me in Bemba", "Ndandisha mu cibemba"),
]
for en, bem in omniglot_bem:
    add_pair(en, bem, "bemba", "omniglot")

# === Omniglot Nyanja/Chichewa phrases (85 entries) ===
omniglot_nya = [
    ("Welcome", "Zikomo"), ("Hello", "Moni"),
    ("How are you?", "Muli bwanji?"), ("I'm fine, how are you?", "Ndiri bwino, kaya inu?"),
    ("What's your name?", "Dzina lanu ndani?"), ("My name is ...", "Dzina langa ndi ..."),
    ("Where are you from?", "Mumachokera kuti?"), ("I'm from ...", "Ndimachokera ku ..."),
    ("Good morning", "Mwauka bwanji?"), ("Good afternoon", "Mwaswela bwanji?"),
    ("Good evening", "Mwachoma bwanji"), ("Good night", "Usiku wabwino"),
    ("Sleep well", "Gonani bwino"), ("Goodbye", "Pitani bwino"),
    ("See you later", "Tionana"), ("See you tomorrow", "Tionana mawa"),
    ("Have a nice day", "Mukhale ndi tsiku labwino"),
    ("Have a good journey", "Muyende bwino"), ("Yes", "Inde"),
    ("No", "Iyayi"), ("Maybe", "Kapena"), ("I don't know", "Sindidziwa"),
    ("I understand", "Ndamvetsetsa"), ("I don't understand", "Sindimvetsa"),
    ("Please speak more slowly", "Chonde lankhulani pangono pangono"),
    ("Excuse me", "Pepani"), ("How much is this?", "Ndalama zingati?"),
    ("Sorry", "Pepani"), ("Please", "Chonde"), ("Thank you", "Zikomo"),
    ("Thank you very much", "Zikomo kwambiri"),
    ("Where's the toilet?", "Chimbudzi chili kuti?"),
    ("I love you", "Ndimakukonda"), ("I miss you", "Ndakusowa"),
    ("Go away!", "Choka!"), ("Leave me alone!", "Ndilekeni!"),
    ("Help!", "Mundithandize!"), ("Fire!", "Moto!"), ("Stop!", "Ima!"),
    ("Call the police!", "Itanani a police!"),
    ("Congratulations!", "Zikomo!"),
    ("Do you speak Chichewa?", "Mumalankhula chicheŵa?"),
    ("I'm learning Chichewa", "Ndikuphunzira Chichewa"),
    ("Happy birthday", "Sangalalani pa tsiku la chibadwi chanu"),
]
for en, nya in omniglot_nya:
    add_pair(en, nya, "nyanja", "omniglot")

# === Omniglot Lozi phrases (43 entries) ===
omniglot_loz = [
    ("Welcome", "Mu amuhezwi"), ("Hello", "Lumela"),
    ("How are you?", "U pila cwang?"), ("I'm fine", "Na pila hande"),
    ("What's your name?", "Libizo lahao ki mang'i?"),
    ("My name is ...", "Libizo laka ki ..."), ("Where are you from?", "U zwa kai?"),
    ("I'm from ...", "Ni zwa kwa ..."), ("Pleased to meet you", "Ki buitumela ku zibana"),
    ("Good morning", "Lumela"), ("Good afternoon", "Ki musihali"),
    ("Good evening", "Lobala ka kozo"), ("Goodbye", "Zamaya sesinde"),
    ("Have a nice day", "Ube ni lizazi lelinde"),
    ("Have a good journey", "U zamaye hande"),
    ("I don't understand", "Ni ni utwisisi"),
    ("Please speak more slowly", "Bulela ka bunya"),
    ("Do you speak Lozi?", "Na wa bulela seRotse?"),
    ("Excuse me", "Ni kupa swalelo"), ("How much is this?", "Ki bukai?"),
    ("Sorry", "Ni swalele"), ("Thank you", "Ni itumezi"),
    ("Where's the toilet?", "Simbuzi si kai?"),
    ("I love you", "Na ku lata"), ("Get well soon", "U fole ka putako"),
    ("Go away!", "Zwa!"), ("Leave me alone!", "U ni tuhele"),
    ("Help!", "Ni tuse!"), ("Fire!", "Mulilo!"), ("Stop!", "Yema!"),
    ("Call the police!", "Biza mapolisa!"),
]
for en, loz in omniglot_loz:
    add_pair(en, loz, "lozi", "omniglot")

# === Lughayangu Bemba (96 entries) ===
lugha_bem = [
    ("Good evening", "cungulo mukwai"), ("Good morning", "mwashibukeni"),
    ("Good afternoon", "mwapoleni"), ("How are you?", "muli shani?"),
    ("I am fine", "tuli bwino"), ("Have a good day", "mwende bwino"),
    ("Nice to meet you", "cawama ukukumana"), ("See you soon", "twalamonana"),
    ("I love you", "nalimitemwa"), ("I miss you", "ndemifuluka"),
    ("You are beautiful", "muli basuma"), ("My love", "mutemwiko wandi"),
    ("I need you", "ndemikabila"), ("I will marry you", "nkamyupa"),
    ("You are mine", "uli wandi"), ("Where are you?", "Muli kwisa?"),
    ("Where do you live?", "mwikala kwisa?"), ("Where are you going?", "muleya kwisa?"),
    ("How much?", "shinga?"), ("What is your name?", "nimwebo ba nani ishina?"),
    ("What are you doing?", "ninshi mulecita?"),
    ("Are you okay?", "muli fye bwino?"), ("When are you coming?", "muleisa lisa?"),
    ("How is your family?", "balishani ku nganda?"),
    ("What is wrong?", "cinshi cilecitika?"), ("What is this?", "ni cinshi?"),
    ("Can I go home?", "kuti naya ku nganda?"),
    ("Happy birthday", "mwafyalweni"), ("Thank you", "Twatotela"),
    ("I am sorry", "ndelomba ubwelelo"), ("You are welcome", "eya mukwai"),
    ("God bless you", "Lesa amipale"), ("Please help me", "ngafweniko"),
    ("I don't know", "shishibe"), ("I will come tomorrow", "nkesa mailo"),
    ("Come here!", "iseni kuno"), ("Leave me alone", "ndekeni nemwine"),
    ("It is okay", "cilifye bwino"), ("I am going home", "ndeya ku nganda"),
    ("I don't want", "shilefwaya"), ("Welcome home", "Mwaiseni"),
    ("God is good", "lesa musuma"), ("I don't understand", "shi umfwile"),
    ("I don't have money", "shikwete indalama"), ("I am done", "napwisha"),
    ("Happy new year", "caka cipya"), ("No problem", "Tapali umulandu"),
    ("Rest in peace", "mulale mucibote"),
    ("I really appreciate it", "natotela sana"),
]
for en, bem in lugha_bem:
    add_pair(en, bem, "bemba", "lughayangu")

# === KitweOnline misc entries ===
kitwe_misc = [
    ("I", "Ine"), ("You", "Iwe"), ("We", "Ifwe"),
    ("Come", "Isa"), ("Follow me", "Nkonka"), ("Sleep now", "Sendama nombaline"),
    ("Eat now", "Lya nombaline"), ("House", "Ing'anda"), ("Family", "Ulupwa"),
    ("Stream", "Mumana"), ("Poison", "Busungu"), ("Free", "Lubuka"),
    ("Change", "Pindulula"), ("Purpose", "Umulandu"), ("Enough", "Linga"),
    ("Jealous", "Akaso"), ("Now", "Nomba"),
]
for en, bem in kitwe_misc:
    add_pair(en, bem, "bemba", "kitweonline")

# Sort and save
dictionary.sort(key=lambda e: e["english"].lower())
DICT_PATH.write_text(json.dumps(dictionary, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Added: {added} new entries")
print(f"Updated: {updated} existing entries with new languages")
print(f"Dictionary total: {len(dictionary)} entries")
