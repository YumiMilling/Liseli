"""Round 2: Merge KitweOnline full dictionary + Tonga Words PDF + misc sources"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DICT_PATH = ROOT / "public" / "data" / "dictionary.json"

dictionary = json.loads(DICT_PATH.read_text(encoding="utf-8"))
by_english = {e["english"].lower(): e for e in dictionary}
added = 0
updated = 0

def add(english, local, language, source, status="verified"):
    global added, updated
    en_key = english.lower().strip()
    local = local.strip()
    if not en_key or not local or len(en_key) < 2 or len(local) < 2:
        return
    if len(local) > 60 or len(english) > 80:
        return
    if " / " in local:
        local = local.split(" / ")[0].strip()
    local = re.sub(r'\s*\([^)]*\)\s*', ' ', local).strip()

    if en_key in by_english:
        entry = by_english[en_key]
        if language not in entry.get("translations", {}):
            entry.setdefault("translations", {})[language] = {
                "text": local, "status": status, "source": source,
            }
            updated += 1
    else:
        entry = {"english": english.strip(), "translations": {
            language: {"text": local, "status": status, "source": source}
        }}
        dictionary.append(entry)
        by_english[en_key] = entry
        added += 1

# === KitweOnline Ab-Ax ===
for pair in "Abdomen=Ifumo|Above=Pa mulu|Absent=Tapali|Abuse=Umusalula|Accept=Pokelela|Accident=Ishamo|Accompany=Shindika|Ache=Kalipa|Add=Lunda|Adhere=Kambatila|Admire=Kumbwa|Admit=Sumina|Admonish=Konkomesha|Adore=Pepa|Adult=Umukulu|Adulterer=Umucende|Adultery=Ubucende|Advance=Tangisha|Advice=Ifunde|Aeroplane=Indeke|Afraid=Tinya|After=Kuntanshi|Afternoon=Icungulo|Again=Nakabili|Against=Kupata|Age=Imyaka|Agree=Sumina|Agreement=Icumfwano|Agriculture=Ubulimi|Ahead=Kuntanshi|Aid=Ubwafwilisho|Aim=Tonta|Air=Umwela|Alarm=Tinya|Alert=Cebusha|Alien=Umweni|Alike=Palana|Alive=Mumi|All=Onse|Allow=Suminisha|Almighty=Wa maka yonse|Almost=Mu cikanga|Alone=Eka|Already=Kale|Also=Na|Alter=Alula|Always=Pe na pe|Amaze=Sungusha|Amend=Wamya|Among=Pa kati ka|Amputate=Putula|Amuse=Sekesha|Ancestor=Icikolwe|Ancient=Kale|And=Na|Angel=Malaika|Anger=Ubukali|Animal=Inama|Ankle=Inkolokoso|Annoy=Kalifya|Another=Umbi|Answer=Asuka|Ant=Nyelele|Antbear=Nengo|Anthill=Iculu|Anxiety=Isakamiko|Any=Onse|Apart=Eka|Ape=Kolwe|Apologize=Papata|Apostle=Umutumishi|Appear=Moneka|Appetite=Insala|Appoint=Sonta|Approach=Palamika|April=Shinde|Argue=Talika|Arm=Ukuboko|Armpit=Mukwapa|Army=Ifila|Around=Mumbali|Arrange=Pekanya|Arrest=Ikata|Arrive=Fika|Arrogance=Icilumba|Arrow=Umufwi|Ascend=Nina|Ashamed=Ba ne nsoni|Ashes=Imito|Ask=Ipusha|Asleep=Lala|Assault=Ulubuli|Assemble=Longana|Assent=Sumina|Assist=Afwa|Attach=Kambatika|Attempt=Esha|Authority=Amaka|Avenge=Landula|Avoid=Taluka|Await=Pemba|Awake=Shibuka|Awaken=Shibusha|Aware=Ishiba|Away=Ukutali|Axe=Isembe".split("|"):
    en, bem = pair.split("=", 1)
    add(en.strip(), bem.strip(), "bemba", "kitweonline")

# === KitweOnline Ba-By ===
for pair in "Baby=Umwana|Bachelor=Umushimbe|Back=Inuma|Bad=Bipa|Bag=Umufuko|Bald=Ipala|Ball=Umupila|Bamboo=Ulusengu|Banana=Inkonde|Bandage=Insalu|Banish=Tamfya|Baptism=Ulubatisho|Bare=Fula|Bark=Icipapa|Barn=Ubutala|Barrel=Umutungi|Basin=Ibeseni|Basket=Umuseke|Bat=Akasusu|Bathe=Samba|Battle=Ubulwi|Beach=Lulamba|Bead=Ubulungu|Beak=Umulomo|Beam=Umwalo|Bean=Cilemba|Beard=Umwefu|Beast=Icinama|Beat=Uma|Beautiful=Suma|Because=Pantu|Become=Sanguka|Bed=Ubusanshi|Bee=Ulushimu|Beer=Ubwalwa|Beetle=Akashishi|Before=Pa ntanshi|Beg=Lomba|Beggar=Umupushi|Begin=Tampa|Beginning=Intendekelo|Behave=Tekanya|Behind=Ku numa|Believe=Sumina|Bell=Inyenjele|Belly=Ifumo|Beloved=Umutemwika|Below=Mwisamba|Belt=Umushipi|Bench=Imbao|Bend=Peta|Benefit=Wamina|Beside=Mupepi|Best=Wamisha|Better=Wama ukucila|Between=Pakati ka|Bible=Icipingo|Bicycle=Incinga|Big=Kalamba|Bind=Kaka|Bird=Icuni|Birth=Ukufyalwa|Bite=Suma|Bitter=Lula|Black=Fita|Blacksmith=Kafula|Bladder=Icisu|Blanket=Ubulangeti|Blaze=Lubingu|Bleed=Suma umulopa|Bless=Pala|Blind=Pofula|Blindness=Ubupofu|Blink=Kapa|Blister=Icitusha|Blood=Umulopa|Bloom=Satula|Blow=Puta|Blunt=Fupa|Board=Ipulanga|Boast=Itakisha|Boat=Ubwato|Body=Umubili|Boil=Bila|Bold=Pama|Bone=Ifupa|Book=Icitabo|Boot=Insapato|Border=Umupaka|Bore=Tula|Born=Fyalwa|Borrow=Ashima|Both=Fyonse|Bottle=Umusukupala|Bounce=Tama|Boundary=Umupaka|Bow=Ubuta|Bowl=Imbale|Box=Imbokoshi|Boy=Umulumendo|Bracelet=Icinkwingili|Brain=Bongo bongo|Branch=Umusambo|Brave=Shipa|Bread=Umukate|Break=Putula|Breakfast=Ikula|Breast=Ibele|Breath=Umupu|Breathe=Pema|Breed=Sanda|Brick=Itafwali|Bridge=Ubulalo|Bright=Beka|Bring=Leta|Broad=Lepa|Broken=Tobeka|Brook=Akamana|Broom=Iceswa|Brother=Ndume|Bruise=Cena|Brush=Cifuti|Bubble=Selauka|Bucket=Imbeketi|Bud=Ulutombo|Buffalo=Imboo|Build=Kula|Bullet=Cipolopolo|Bundle=Umwanshi|Burden=Icipe|Burn=Oca|Burst=Lepuka|Bury=Shika|Bush=Impanga|Bushbuck=Cisongo|Business=Umulimo|Butcher=Kakoma wa ngombe|Butter=Amafuta ye shiba|Butterfly=Icipelebesha|Buttock=Itako|Button=Ipitawa|Buy=Shita".split("|"):
    en, bem = pair.split("=", 1)
    add(en.strip(), bem.strip(), "bemba", "kitweonline")

# === KitweOnline Pa-Py ===
for pair in "Pack=Longa|Pain=Bukali|Paint=Lenga|Palm=Lupi|Pant=Pemekesha|Paper=Ipepala|Pardon=Luse|Parent=Mufyashi|Parrot=Mucence|Part=Cipande|Pass=Pita|Passport=Pasu|Past=Kale|Path=Nshila|Patience=Kushipikisha|Paw=Lukasa|Pay=Malipilo|Pea=Ntongwe|Peanut=Lubalala|Peanut butter=Cikonko|Peace=Cibote|Peck=Sompa|Peel=Pala|Pen=Nibu|Penalty=Mafuto|Pencil=Pensulo|People=Bantu|Pepper=Mpilipili|Perfect=Suma sana|Person=Muntu|Perspiration=Ibe|Petrol=Petulo|Picture=Nsalamu|Piece=Cipande|Pig=Nkumba|Pigeon=Nkunda|Pillow=Musao|Pinch=Shina|Pineapple=Cinanashi|Pipe=Paipi|Pity=Luse|Place=Ncende|Plant=Byala|Plate=Mbale|Play=Angala|Please=Papata|Pleasure=Nsansa|Plenty=Bwingi|Plough=Lukasu|Pluck=Saba|Poison=Busungu|Police=Kapokola|Pool=Cishiba|Poor=Landa|Porridge=Musunga|Pot=Nongo|Potato=Cilashi|Potato sweet=Cumbu|Potter=Nakabumba|Pour=Itila|Poverty=Bupina|Powder=Bunga|Power=Maka|Praise=Tasha|Pray=Pepa|Prayer=Isali|Preach=Funda|Prepare=Pekanya|Present=Bupe|President=Kateka|Press=Tininkisha|Pretend=Cita nga|Prevent=Lesha|Price=Mutengo|Pride=Cilumba|Priest=Shimapepo|Prison=Cifungo|Prisoner=Nkole|Profit=Mwenamo|Prohibit=Kanya|Promise=Cilayo|Proof=Cishinino|Prophet=Kasesema|Protect=Sunga|Prove=Shininkisha|Proverb=Ipinda|Pull=Tinta|Pump=Pompi|Punish=Panika|Pupil=Musambilila|Purchase=Shita|Pure=Nkonko|Purpose=Mulandu|Push=Sunka|Put=Bika|Puzzle=Sungusha|Python=Lusato".split("|"):
    en, bem = pair.split("=", 1)
    add(en.strip(), bem.strip(), "bemba", "kitweonline")

# === KitweOnline Ta-Ty ===
for pair in "Table=Itebulo|Taboo=Mwiko|Tail=Mucila|Tailor=Kabila|Take=Bula|Talk=Ilyashi|Tall=Lepa|Tame=Belesha|Tank=Tanki|Task=Mulimo|Taste=Sonda|Tax=Musonko|Tea=Ti|Teach=Funda|Teacher=Kafundisha|Tear=Lepula|Tease=Konya|Tell=Eba|Tempt=Pimpila|Ten=Ikumi|Tender=Naka|Tent=Tenti|Test=Esha|Thank=Totela|Theft=Bupupu|Thick=Kulu|Thief=Mupupu|Thigh=Itanta|Thin=Onda|Thing=Cintu|Think=Tontonkanya|Thirst=Cilaka|Thorn=Munga|Thought=Muntontonkanya|Thousand=Ikana limo|Thread=Bushishi|Threaten=Tinya|Three=Tatu|Throat=Cikolomino|Throw=Posa|Thumb=Cikumo|Thunder=Nkuba|Tick=Lukufu|Ticket=Itikiti|Tickle=Tekunya|Tie=Kaka|Time=Nshita|Tin=Cikopo|Tiny=Ubuce|Tired=Naka|Today=Lelo|Toe=Cikondo|Together=Pamo|Tomato=Matimati|Tomb=Cilindi|Tomorrow=Mailo|Tongue=Lulimi|Tool=Cibombelo|Tooth=Lino|Toothache=Muca|Top=Mulu|Torch=Lusaniko|Tortoise=Fulwe|Touch=Kumya|Tough=Kosa|Towel=Citambala|Town=Musumba|Trade=Lukwebo|Train=Shitima|Translate=Alula|Trap=Citeyo|Travel=Tandala|Traveller=Mulendo|Treasure=Cuma|Tree=Muti|Tremble=Tutuma|Tribe=Mutundu|Trouble=Bwafya|Trousers=Itoloshi|True=Cine|Trumpet=Ipenga|Trunk=Mukonso|Trust=Cetekela|Truth=Cumi|Try=Esha|Tuberculosis=Ntanda-bwanga|Turn=Pilibula|Turtle=Fulwe|Twice=Miku ibili|Twist=Nyonga|Two=Bili|Type=Musango|Tyre=Mupeto".split("|"):
    en, bem = pair.split("=", 1)
    add(en.strip(), bem.strip(), "bemba", "kitweonline")

# === KitweOnline Na-Nyu (Bemba words as English keys) ===
for pair in "Bride=Nabwinga|Midwife=Nacimbusa|Virgin=Nacisungu|Potter=Nakabumba|Quail=Nakabundu|Meek=Nakilila|Gum=Namba|Driver=Namutekenya|Lazy=Nangana|Companion=Nankwe|Cook mush=Naya|Strainer=Ncemeko|Jaw=Ncendwa|Cork=Nciliko|Louse=Nda|Medicine=Ndawa|Advocate=Ndubulwila|Giraffe=Ndyabuluba|Witchdoctor=Ng'anga|Crab=Ng'anse|Wheat=Ng'anu|Crocodile=Ng'wena|Dike=Ngalande|Rust=Ngalawa|Camel=Ngamiya|Cobra=Ngoshe|Wild pig=Ngulube|Dambo=Nika|Climb=Nina|Cat=Nyau|Candle=Nyali|Cricket=Nyense|Newspaper=Nyunshi|Lion=Nkalamo|Skin=Nkanda|Chicken=Nkoko|Snail=Nkola|Ankle=Nkolokoso|Debt=Nkongole|Elbow=Nkonkoni|Walking stick=Nkonto|Lightning=Nkuba|Dandruff=Nkuku|Pig=Nkumba|Pigeon=Nkunda|Fish-eagle=Nkwashi|Shield=Nkwela|Hunger=Nsala|Cloth=Nsalu|Pleasure=Nsansa|Path=Nshila|Cemetery=Nshinshi|Time=Nshita|Elephant=Nsofu|Snake=Nsoka|Bashfulness=Nsoni|Proverb=Nsoselo|Gourd=Nsupa|Rope=Ntambo|Tuberculosis=Ntanda-bwanga|Snuff box=Ntekwe|Curse=Ntipu|Pea=Ntongwe|Source=Ntulo|Leader=Ntungulushi|Temptation=Ntunko|Dwarf=Ntuse|Peanut butter=Ntwilo".split("|"):
    en, bem = pair.split("=", 1)
    add(en.strip(), bem.strip(), "bemba", "kitweonline")

# === Tonga Words PDF ===
for pair in "How are you=Mwapona|Good=Kabotu|Thank you=Twalumba|Water=Meenda|Food=Chakulya|Good morning=Mwabuka buti|Yes=Eee|No=Peepe|Child=Mwana|Brother=Mukulana|Mother=Bama|Father=Ndende|Uncle=Tatlenzi|See you tomorrow=Nzokubona junza|Ladies=Banakazi|Men=Balumi|Eyes=Meso|Nose=Impemo|Teeth=Meno|Think=Yeya|Run=Cijana|Talk=Wambula|Laugh=Seka|Bicycle=Camutuntendelele|Car=Imota|Goat=Mpongo|Sheep=Impelele|Goodbye=Mucaale kabotu|Come here=Kweza|Drink=Nywa|Today=Sunu|Tomorrow=Junza".split("|"):
    en, toi = pair.split("=", 1)
    add(en.strip(), toi.strip(), "tonga", "tonga_words_pdf")

# === Victoria Falls travel Nyanja ===
for pair in "Chicken=Nkuku|Fish=Nsomba|Bread=Buledi|Rice=Mpunga|Eggs=Mazira|One=Modzi|Two=Wiri|Three=Tatu|Ten=Khumi|Sir=Abambo|Madam=Amayi".split("|"):
    en, nya = pair.split("=", 1)
    add(en.strip(), nya.strip(), "nyanja", "victoriafalls_travel")

# Sort and save
dictionary.sort(key=lambda e: e["english"].lower())
DICT_PATH.write_text(json.dumps(dictionary, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Added: {added}")
print(f"Updated: {updated}")
print(f"Total: {len(dictionary)}")
