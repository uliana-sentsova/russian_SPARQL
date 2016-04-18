import os
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from pymystem3 import Mystem
m = Mystem()
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

# ======================================

pwd = os.getcwd()
os.chdir(pwd + "/CONFIG")
LOCATION_DICTIONARY = dict()
with open("RU-EN.txt", 'r', encoding="utf-8") as f:
    for line in f:
        LOCATION_DICTIONARY[line.split("\t")[0]] = line.strip().split("\t")[1]

PROPERTIES = dict()
with open("PROP.txt", "r", encoding="utf-8") as g:
    for line in g:
        line = line.strip().split(",")
        PROPERTIES[line[0]] = line[1]
        # PROPERTIES[line[1]] = [l for l in line[0].split(",")]

os.chdir(pwd)
pwd = os.getcwd()

# ======================================
# Функция импортирует шаблон.
def open_pattern(filename):
    os.chdir(pwd + "/Patterns")
    with open(filename, 'r') as pattern:
        pattern = pattern.read()
    return pattern

# Вспомогательная функция для проверки, является ли токен словом,
# а не знаком пунктуации или цифрами.
def is_word(word):
    assert type(word) == str
    for symbol in word:
        if symbol not in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя":
            return False
    return True


# Вспомогательная функция
def reordered(bigram):
    bigram = bigram.split(" ")
    bigram = bigram[1] + " " + bigram[0]
    return bigram


# Вспомогательная функция для поиска биграммов в словаре локаций
# (чтобы находить такие локации как "новосибирская область").
def search_bigram(words_list):
    locations = []
    bigrams = []
    for i in range(0, len(words_list)):
        try:
            bigrams.append(words_list[i] + " " + words_list [i + 1])
        except IndexError:
            break
    for bigram in bigrams:
        if bigram in LOCATION_DICTIONARY:
            locations.append(bigram)
    if not locations:
        for bigram in bigrams:
            if reordered(bigram) in LOCATION_DICTIONARY:
                locations.append(bigram)
    return locations

# Функция ищет локацию в запросе: сначала отдельные слова, затем биграммы.
# На вход нужно подавать лемматизированный array.
def find_location(words_list):
    locations = []
    for word in words_list:
        if word in LOCATION_DICTIONARY:
            locations.append(word)
    if not locations:
        return search_bigram(words_list)
    else:
        return locations


# Функция переводит запрос на язык DPBedia: Липецк -> Lipetsk
def translate_location(location):
    return LOCATION_DICTIONARY[location[0]]


# Функция проверяет потенциальный предикат на наличие в словаре предикатов.
def is_in_properties(query):
    if query in PROPERTIES.keys():
        return PROPERTIES[query]
    else:
        return False


# Функция лемматизирует запрос, находит в нем локацию, находит потенциальный предикат,
# проверяет его в словаре предикатов (функция is_in_properties).
def analyze_input(input_query):
    assert type(input_query) == str
    lemmas = m.lemmatize(input_query.lower())
    lemmas = [l for l in lemmas if is_word(l)]
    try:
        location = find_location(lemmas)
        print("Локация: ", location)
        rest = re.sub(location[0], "", " ".join(lemmas)).strip()
        predicate = is_in_properties(rest)
        return (translate_location(location), predicate)
    except KeyError:
        print("KeyError: Location is not in the dictionary.")


# Функция создает запрос. На вход подаётся субъект (локация),
# переменная (неизвестная информация), предикат и шаблон запроса.
def construct_query(subject, variable, predicate, query):
    query = query.replace("SUBJECT", subject)
    query = query.replace("VARIABLE", variable)
    query = query.replace("PREDICATE", predicate)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    final = []
    for result in results["results"]["bindings"]:
        final.append(result[variable]["value"])
    return query, final


# TODO: написать функцию, выбирающая имя для переменной variable в зависимости от характера запроса.

# TODO: написать функцию, подобную pattern-handler'у из бутстреппинга, чтобы одинаково мэтчились фразы "в берлине",
# TODO: "берлина", "берлин"

# TODO: подумать, как сделать функцию выбора шаблона sparql

# TODO: написать грамматику, которая делает из простой локации разные варианты (новосибирск, город новосибирск)


# Делаем запрос
def make_query(query):
    # Открываем шаблоны
    pattern1 = open_pattern("pattern1.txt")
    pattern2 = open_pattern("pattern2.txt")
    print("\n")
    print("ЗАПРОС:")
    print(query)
    print("------------------------------------------------------------")
    (subject, predicate) = analyze_input(query)
    sparql_query, result = construct_query(subject=subject, variable="variable", predicate=predicate, query=pattern1)
    if not result:
        sparql_query, result = construct_query(subject=subject, variable="variable", predicate=predicate, query=pattern2)
    print("РЕЗУЛЬТАТ ЗАПРОСА: ")
    for r in result:
        print(r)
    print("\n" + "ТЕЛО ЗАПРОСА: ")
    print("------------------------------------------------------------")
    print(sparql_query)
    print("------------------------------------------------------------")



query1 = "На какой широте и долготе расположен Берлин?"
query2 = "В каком экономическом регионе находится Москва?"
query3 = "Какое население в Берлине?"

make_query(query1)
make_query(query2)
make_query(query3)
