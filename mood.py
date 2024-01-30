import re
import pymorphy3
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
# для проверки наличия файла с текстом (т.к. ввод осуществляется пользователем)
from os.path import isfile

# Подключаем морфологический анализатор
morph = pymorphy3.MorphAnalyzer()

# Обрабатываем словарь тональностей
df = pd.read_csv('kartaslovsent.csv', encoding='utf-8', sep=';')
sentiment_dict = dict(zip(df['term'], df['value']))


# Подключение и расширения списка стоп-слов
def stop_words_set():
    stop_words = stopwords.words('russian')
    stop_words.remove('не')
    stop_words.extend(
        ['это', 'эти', 'этот', 'эта', 'ней', 'тот', 'те', 'то', 'им', 'ей', 'из', 'к', 'ах', 'эй'])
    stop_words.extend(
        ['ох', 'её', 'ещё', 'кто', 'кто-то', 'мой', 'твой', 'мы', 'наш', 'он', 'свой', 'сам', 'такой', 'ты', 'ваш'])
    stop_words.extend(
        ['что-то', 'что-нибудь', 'ай', 'ой', 'мы', 'кто-нибудь', 'все-таки'])
    return set(stop_words)

def statistics_out(sentiment_counter, total_word_count, unique_word_count, top_word):
    print('\n----------------Statistics--------------------')
    print(f">>> Число положительных слов: {sentiment_counter['Позитивный']}")
    print(f">>> Число отрицательных слов: {sentiment_counter['Негативный']}")
    print(f">>> Число нейтральных слов: {sentiment_counter['Нейтральный']}")
    print(f">>> Общее число словоупотреблений: {total_word_count}")
    print(f">>> Число различных (уникальных) слов: {unique_word_count}")
    print(f">>> Пять самых частотных слов в тексте:")
    for word, freq in top_word:
        print(f"\t · {word}: {freq}")

def sentiment_out(sentiment_score, sentiment_counter):
    print(f">>> Тональная окраска текста (средняя тональность слов): {sentiment_score:.4f}")
    print(
        f">>> Тональная окраска текста (на основе количества тональных слов): {max(sentiment_counter, key=sentiment_counter.get)}")
    print(f">>> Тональная окраска текста (как комбинация двух мер): ", end='')
    if sentiment_score > 0:
        if max(sentiment_counter, key=sentiment_counter.get) == 'Позитивный':
            print('Позитивный')
        else:
            print('Скорее позитивный')
    elif sentiment_score < 0:
        if max(sentiment_counter, key=sentiment_counter.get) == 'Негативный':
            print('Негативный')
        else:
            print('Скорее негативный')
    else:
        print('Нейтральный')
    print('\n')


# Функция для вывода стиля текста
def styles_out(sentiment_sc, sentiment_count, total_word_counter):
    if sentiment_count['Нейтральный'] / total_word_counter > 0.5:
        print(">>> Текст написан в научно-деловом стиле")
    elif abs(sentiment_sc) > 0.3 or abs(sentiment_sc) < 0.11:
        print(">>> Текст написан в художественном стиле")
    elif sentiment_count['Нейтральный'] / total_word_counter < 0.5 or (abs(sentiment_sc) < 0.29):
        print(">>> Текст написан в публицистическом стиле")

# Функция анализа текста на тональности
def analyze_sentiment(lemmas, sentiment_dict, sentiment_counter, word_frequency):
    sentiment_score = 0
    total_words = 0
    flag = False

    for index, lemma in enumerate(lemmas):
        if lemma == 'не' and index + 1 < len(lemmas) and sentiment_dict.get(lemmas[index + 1], 0):
            flag = True
        elif lemma in sentiment_dict:
            l_index = df[df.term == lemma].index[0]
            if flag == True:
                sentiment_score += (-1) * sentiment_dict[lemma]
                if (sentiment_dict[lemma] > 0):
                    sentiment_counter['Негативный'] += 1
                else:
                    sentiment_counter['Позитивный'] += 1
                flag = False
            elif df.tag[l_index] == 'PSTV':
                sentiment_counter['Позитивный'] += 1
            elif df.tag[l_index] == 'NGTV':
                sentiment_counter['Негативный'] += 1
            elif df.tag[l_index] == 'NEUT':
                sentiment_counter['Нейтральный'] += 1
            sentiment_score += sentiment_dict[lemma]

        word_frequency[lemma] += 1
        total_words += 1

    return sentiment_score / total_words if total_words > 0 else 0


global cont
cont = 'y'

while cont == 'y':
    output_counter = 1

    word_frequency = Counter()

    # Открываем файл с текстом и производим предобработку
    filename = input('\n>>> Введите имя файла, из которого нужно прочитать текст ')

    while not isfile(filename):
        print(f">>> Файл с имененм {filename} не найден!\n")
        filename = input(">>> Введите имя файла: ")


    file = open(filename, 'r', encoding='utf-8')
    text = file.read().lower()

    # Токенезируем текст и очищаем его от знаков препинания
    tokens = word_tokenize(text, language='russian')
    tokens = [token for token in tokens if re.match(r'^[а-яА-ЯёЁ0-9\s]+$', token)]

    stop_flag = input(">>> Хотите удалить стоп-слова из текста? (y/n) ")

    if stop_flag == 'y':
        # Создаем список стоп-слов
        set_stop = stop_words_set()
        lemmas = [morph.parse(token)[0].normal_form for token in tokens if morph.parse(token)[0].normal_form not in set_stop]
    elif stop_flag == 'n':
        # Приводим токены к леммам для корректного подсчета тональной оценки
        lemmas = [morph.parse(token)[0].normal_form for token in tokens]


    # Создаем словарь в который будем записывать количество слов определенной тональности
    sentiment_counter = {'Позитивный': 0, 'Негативный': 0, 'Нейтральный': 0}

    # Вызываем функцию выполняющую тональную оценку текста
    sentiment_score = analyze_sentiment(lemmas, sentiment_dict, sentiment_counter, word_frequency)

    # Статистические подсчеты
    total_word_count = len(tokens)
    unique_words = set(lemmas)
    unique_word_count = len(unique_words)
    top_word = word_frequency.most_common(5)

    # Выводим тональные оценки
    sentiment_out(sentiment_score, sentiment_counter)

    # Выводим стиль текста
    styles_out(sentiment_score, sentiment_counter, total_word_count)

    # Выводим статистику по тексту
    statistics_out(sentiment_counter, total_word_count, unique_word_count, top_word)

    x = input('>>> Хотите получить подробный морфологический анализ слов текста? (y/n) ')
    if x == 'y':
        morp_analysis = [morph.parse(token)[0] for token in tokens]
        with open(f'morp_analysis{output_counter}.txt', 'w', encoding='utf-8') as output:
            for el in morp_analysis:
                out_line = f'Слово - {el.word}; часть речи - {el.tag.POS}; нормальная форма слова - {el.normal_form} \n'
                output.write(out_line)
        print(f'>>> Подробный морфологический анализ слов текста успешно записан в файл morp_analysis{output_counter}.txt\n')
        output_counter += 1
    file.close()

    cont = input('>>> Хотите продолжить работу с программой? (y/n) ')
