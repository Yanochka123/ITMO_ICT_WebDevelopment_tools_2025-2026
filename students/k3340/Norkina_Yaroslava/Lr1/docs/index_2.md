# Лабораторная работа №2. Потоки. Процессы. Асинхронность.
Цель работы: понять отличия потоками и процессами и понять, что такое ассинхронность в Python.

### Термины
В вычислительной технике процесс — это выполняющийся экземпляр компьютерной программы.

Поток — это объект внутри процесса, выполнение которого можно запланировать. Кроме того, это наименьшая единица обработки, которую можно выполнить в ОС (операционной системе). Проще говоря, поток — это последовательность таких инструкций внутри программы, которая может выполняться независимо от другого кода. Для простоты можно предположить, что поток — это просто подмножество процесса.

Блок управления потоком: содержит в себе Идентификатор потока, Указатель стека, Счетчик программы, состояние потока, набор регистров потока, указатель родительского процесса.

<img width="918" height="540" alt="image" src="https://github.com/user-attachments/assets/b7d16afa-9291-417f-8c5c-ba1c0af23c01" />

Многопоточность определяется как способность процессора одновременно выполнять несколько потоков.

Переключением контекста - частое переключение между потоками.

Многозадачность - переключение контекста, происходящее настолько часто, что кажется, что все потоки выполняются параллельно

Многопоточность в Python.
	1) Импортируется модуль потоковой обработки.
	import threading
	2) Создается объект класса Thread
Целью является функция, которая будет выполняться потоком, тогда как аргументы — это аргументы, которые должны быть переданы целевой функции.
t1 = threading.Thread(target, args)
t2 = threading.Thread(target, args)
	3) Чтобы запустить поток, используется метод start() класса Thread.
	4) Чтобы остановить выполнение текущей программы до завершения потока, используется метод join().


<img width="831" height="617" alt="image" src="https://github.com/user-attachments/assets/fbec6799-8777-47c4-9c2b-7dd6e02c5bbf" />

Состояние гонки (race condition) - состояние, когда два или более потока пытаются изменить общее состояние, такое как переменная, одновременно, что приводит к непредсказуемым результатам.

## Задание:
#### Задача 1. Различия между threading, multiprocessing и async в Python  
Задача: Напишите три различных программы на Python, использующие каждый из подходов: threading, multiprocessing и async. Каждая программа должна решать считать сумму всех чисел от 1 до 10000000000000. Разделите вычисления на несколько параллельных задач для ускорения выполнения.

Целевая функция calculate_sum создает интенсивную нагрузку на процессор путем сложения чисел. Сложность вычислений составляет O(N):

def calculate_sum(start: int, end: int) -> int:
    total = 0
    for i in range(start, end + 1):
        total += i
    return total

1.1. Многопоточный подход (threading)
Используется библиотека threading: особенностью является разделение целевой переменной, которая подается на вход в каждый новый созданный поток. Так как потоки пользуются общими данными, они не должны обращаться и изменять просто так одну и ту же переменную. Поэтому результаты всех вызовов записываются в массив и уже после всех вычислений суммируются.
``` Python
thread = threading.Thread(target=calculate_sum, args=(start, end, results, i))
threads.append(thread)
thread.start() # запуск каждого нового потока 
```
Завершение работы потоков при помощи метода join():
``` Python
	for thread in threads:
        thread.join() # ожидание результата от всех потоков и завершение работы
            
result = sum(results)
``` 
1.2 Multiprocessing
При помощи библиотеки создается пул задач, состоящий из выполняемой функции и пар аргументов на вход к этой функции (tuple). Затем в созданных процессах - по количеству выполняемых задач, происходит расчет результатов:
``` Python
    # использование библиотеки multiprocesing
    with multiprocessing.Pool(processes=num_tasks) as pool:
        results = pool.map(calculate_sum, tasks_args) # принимает в качестве аргументов целевую 
        # функцию и ее аргументы на вход единственной переменной
```

1.3 Async
Особенности реализации заключаются в использовании библиотеки asyncio, а также специальных слов для обозначения асинхронных функций:
``` Python
async def calculate_sum_async(start: int, end: int) -> int:
	...

async def run_asyncio_logic(target_number: int, num_tasks: int):
	...
	tasks.append(calculate_sum_async(start, end))
```
Момент, где программе необходимо дождаться получение результата выполнения асинхронных функций, прежде чем продолжить выполнение остального кода обозначается словом await:
``` Python
results = await asyncio.gather(*tasks)
```
Также необходим непосредственный запуск асинхронной функции через обращение к библиотеке. asyncio.run() — это точка входа, которая создаёт новый event loop (цикл событий), который управляет корутинами. Она также сразу запускает переданную асинхронную функцию внутри этого цикла до её завершения, после чего освобождает ресурсы и закрывает цикл.
``` Python
asyncio.run(run_asyncio_logic(target_number, num_tasks))
```

Тестирование
Наилучший результат показал асинхронный подход на тестовом запуске с небольшим числом N < 10**9
<img width="649" height="320" alt="image" src="https://github.com/user-attachments/assets/b515806c-172c-4ac4-96a7-85da02ea4928" />
<img width="659" height="293" alt="image" src="https://github.com/user-attachments/assets/c083f364-925c-470d-96c2-22d68ea0e92c" />
<img width="682" height="289" alt="image" src="https://github.com/user-attachments/assets/a31e0c77-c69f-4cfb-a5e4-a0006f407028" />



Сравнение результатов работы трех подходов в зависимости от количества используемых подходов.

<img width="741" height="319" alt="image" src="https://github.com/user-attachments/assets/07670576-4e83-4e25-ae5d-fee82ae41f37" />

<img width="752" height="295" alt="image" src="https://github.com/user-attachments/assets/45878990-2c26-484e-87d9-2c8b1fca7fc9" />

<img width="748" height="322" alt="image" src="https://github.com/user-attachments/assets/e15954af-3476-4537-b071-e806db87f769" />

## _Таблица 1. Зависимость от входного числа N (workers = 8)_

| N | Threading, сек | Multiprocessing, сек | Async, сек |
|---|---|---|---|
| 10 000 000 | 0.3073 | 0.3553 | **0.2799** |
| 100 000 000 | 2.7901 | **0.9235** | 2.7404 |
| 1 000 000 000 | 26.8077 | **6.6997** | 27.5780 |

Время Threading и Async при росте N растёт линейно вместе с объёмом работы. Это проявление GIL: потоки и корутины делят один поток исполнения байткода, реального параллелизма нет. Multiprocessing на больших N выигрывает, на маленьком N = 10⁷ результаты хуже, так как сказываются накладные расходы на создание процессов и сериализацию.

## _Таблица 2. Зависимость от количества подходов (фиксированное N)_

| Воркеров | Threading, сек | Multiprocessing, сек | Async, сек |
|---|---|---|---|
| 4 | 26.5970 | **9.8382** | 26.4531 | 
| 8 | 26.8077 | **6.6997** | 27.5780 | 
| 16 | 26.5434 | **5.9632** | 26.8505 | 

Multiprocessing масштабируется, однако ускорение при увеличении числа процессов замедляется. Это связано с ограниченным числом физических ядер CPU и растущими накладными расходами на IPC.
Threading и Async  при любом числе воркеров отрабатывают одинаково. Это демонстрирует GIL и однопоточность вычислений event loop.

Тест на числе N = 10000000000000. В реализации использовалась формула Гаусса для подсчета суммы чисел вместо итеративного подхода из-за слищком большого времени исполнения программы. Threading и Async для выполнения необходимо вызвать функцию, посчитать формулу, сложить — микросекунды.

В то же время Multiprocessing должен создать до 60 полноценных процессов, сериализовать аргументы, отправить их в процессы, собрать результаты обратно.

## _Таблица 3 – Сравнение времени работы трех подходов_

| Подход               | Время с 8 подходами | С 16 подходами    | С 60 подходами    |
| -------------------- | ------------------- | ----------------- | ----------------- |
| **Multiprocessing**  | **0.2329 сек**      | **0.2814 сек**    | **0.5261 сек**    |    
| **Async**            | ~0.0000 сек         | ~0.0000 сек       | 0.0010 сек        |
| **Threading**        | 0.0010 сек          |  0.0010 сек       | 0.0060 сек        |


## Вывод
При использовании итеративного суммирования в функции calculate_sum() multiprocessing показывает единственное реальное ускорение, обходя GIL за счёт отдельных процессов. Threading и asyncio не дают прироста производительности, поскольку выполняются в одном потоке (GIL для потоков, однопоточный event loop для asyncio), и их время линейно зависит от объёма вычислений. Оптимальное число процессов ограничено числом физических ядер CPU: на 8 ядрах переход с 8 на 16 процессов даёт лишь 12% прироста из-за накладных расходов на межпроцессное взаимодействие и конкуренции за ядра.
В результате выполнения задания удалось научиться применять принципы многопоточного и асинхронного программирования, на практике проверить эффективность данных подходов к задаче, требующей больших вычислительных ресурсов. При этом наилучшим образом в ходе экспериментов показал себя многопроцессный подход, но в зависимости от числа процессов общее время рассчета может значительно ухудшаться. Это связано с использованием изолированных ресурсов и сложностей организации такого взаимодействия при запуске программы.


#### Задача 2. Параллельный парсинг веб-страниц с сохранением в базу данных

Задача: Напишите программу на Python для параллельного парсинга нескольких веб-страниц с сохранением данных в базу данных с использованием подходов threading, multiprocessing и async. Каждая программа должна парсить информацию с нескольких веб-сайтов, сохранять их в базу данных.

В задании требовалось разработать программу для параллельного парсинга информации о книгах с нескольких веб-сайтов. Каждая программа должна содержать функцию parse_and_save(url), которая загружает HTML-страницу, парсит ее, выводит результат на экран и сохраняет заголовок с другими данными в базу данных из лабораторной работы №1. Список URL-адресов должен быть предварительно разделен на равные части. Требуется произвести замеры времени выполнения и прокомментировать результаты сравнения.

### Описание решения

Для запуска и загрузки бд необходимо доустановить асинхронный движок:
``` Python
python -m pip install asyncpg
```

Основные файлы в проекте:
url_load.py -  Утилита для предварительного сбора 100 уникальных URL-адресов с сайтов, содержащих задачи, чек-листы и планы. Результат сохраняется в urls.txt. 
parsing.py - Универсальный адаптер-парсер для страниц с задачами или чек-листами. Содержит функцию extract_page_info(html, url) для поиска на странице информации и передачи результата в нужном формате данных.  
db.py - Подключение к базе данных через уже созданные переменные окружения, работает с PostgeSQL при помощи SQLModel и SQLAlchemy. Содержит в себе как обычные функции для создания пользователя, парсера, новых тегов и категорий задач, так и их асинхронные версии.  
main.py - Точка входа для запуска работы всех программ парсера.  


Программы.
Все три файла далее делают одно и то же: парсинг URL и сохранение данных в БД, но вних по-разному реализован параллелизм. 

1. Async_2.py
Используются асинхронная библиотека aiohttp, а также ключевые слова async и await.
Программой создается один поток и event loop, который управляет тысячами одновременных задач.

Aiohttp — асинхронная, так что await отдаёт управление другим корутинам. TCPConnector(limit=30) — ограничение пула TCP-соединений, единая ClientSession переиспользует TCP-соединения.
``` Python
import time
import asyncio
import aiohttp

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_async

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

async def parse_and_save(url: str, session: aiohttp.ClientSession):
    # асинхронная функция использует неблокирующиеся GIL операции ввода-вывода

    for _ in range(3):
        try:
            # Асинхронный HTTP-запрос
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                html = await response.text()
                
                # Извлечение данных
                page_data = extract_page_info(html, url)
                if page_data["title"] == "Без названия":
                    return
                    
                # Асинхронное сохранение в БД
                await save_to_db_async(page_data)
                print(f"[Async] Сохранено: '{page_data['title']}'")
                return
        except (aiohttp.ClientError, asyncio.TimeoutError):
            await asyncio.sleep(1)
        except Exception as e:
            print(f"[Async] Ошибка: {e}")
            return

async def async_worker(urls_chunk: list[str], session: aiohttp.ClientSession):
    tasks = [asyncio.create_task(parse_and_save(url, session)) for url in urls_chunk]
    await asyncio.gather(*tasks)

async def run_async_logic() -> float:
    print("Запуск асинхронности")
    start_time = time.time()
    
    urls = load_urls()
    num_tasks = 8
    chunks = divide_into_chunks(urls, num_tasks)
    
    # Ограничиваем пул одновременных TCP-соединений на уровне коннектора,
    # чтобы избежать отказа в обслуживании (DDoS-эффект) со стороны целевых серверов.
    connector = aiohttp.TCPConnector(limit=30)
    
    # Единая сессия переиспользует базовое TCP-соединение для всех запросов
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        workers = [asyncio.create_task(async_worker(chunk, session)) for chunk in chunks]
        await asyncio.gather(*workers)
        
    elapsed = time.time() - start_time
    print(f"asyncio завершено за {elapsed:.4f} сек\n")
    return elapsed

def run_asyncio() -> float:
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(run_async_logic())
```
При этом функция сохранения данных в БД - асинхронная.

3. Multiprocessing_2.py
Программа создает 8 **процессов** — каждый со своим интерпретатором Python и своим GIL.

В Windows используется spawn: каждый процесс заново импортирует модули и создаёт свой SQLAlchemy engine, что довольно затратно по ресурсам.

Получается создать настоящий параллелизм не ограниченный GIL, но при этом расходы на форк могут составлять 8–16 сек, каждое подключение к БД в процессах свое;

 также должен происходить обмен данными между процессами через pickle.

``` Python
import time
import multiprocessing
import requests
from requests.exceptions import RequestException

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_sync

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def parse_and_save(url: str):
    # Целевая функция загрузки и обработки веб-страницы
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            page_data = extract_page_info(response.text, url)
            if page_data["title"] == "Без названия":
                return
                
            save_to_db_sync(page_data)
            print(f"[Process-{multiprocessing.current_process().name}] Сохранено: '{page_data['title']}'")
            return 
        except RequestException:
            time.sleep(1)
        except Exception as e:
            print(f"[Process-{multiprocessing.current_process().name}] Ошибка: {e}")
            return

def process_worker(urls_chunk: list[str]):
    # Работа процесса
    for url in urls_chunk:
        parse_and_save(url)

def run_multiprocessing() -> float:
    # Многопроцессное выполнение
    print("Запуск процессов")
    start_time = time.time()
    
    urls = load_urls()
    num_processes = 8
    chunks = divide_into_chunks(urls, num_processes)
    processes = []
    
    # Создание изолированных процессов ОС. 
    # В отличие от потоков, процессы требуют больше ресурсов на инициализацию.
    for i, chunk in enumerate(chunks):
        p = multiprocessing.Process(target=process_worker, args=(chunk,), name=str(i+1))
        processes.append(p)
        p.start()
        
    for p in processes:
        p.join()
        
    elapsed = time.time() - start_time
    print(f"multiprocessing - завершено за {elapsed:.4f} сек\n")
    return elapsed
```

5. Threading_2.py
Здесь используется импорт threading и синхронной библиотеки requests, программой создается 8 потоков в одном процессе, при этом остается общий GIL.

Requests — синхронная библиотека, поэтому необходимо каждый поток блокировать на requests.get().

В это время - time.sleep(1), GIL освобождается и дает возможность другим потокам поработать.

Накладными расходами при таком подходе будет переключение контекста потоков.
``` Python
import time
import threading
import requests
from requests.exceptions import RequestException

from parsing import load_urls, divide_into_chunks, extract_page_info
from db import save_to_db_sync

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def parse_and_save(url: str):
    # Целевая функция загрузки и обработки веб-страницы
    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            page_data = extract_page_info(response.text, url)
            if page_data["title"] == "Без названия":
                return
                
            save_to_db_sync(page_data)
            print(f"[Thread-{threading.current_thread().name}] Сохранено: '{page_data['title']}'")
            return 
        except RequestException:
            # При сетевом сбое (таймаут) поток засыпает перед повторной попыткой.
            # Благодаря GIL в этот момент управление передается другому потоку.
            time.sleep(1) 
        except Exception as e:
            print(f"[Thread-{threading.current_thread().name}] Ошибка: {e}")
            return

def thread_worker(urls_chunk: list[str]):
    # Работа потока
    for url in urls_chunk:
        parse_and_save(url)

def run_threading() -> float:
    # Начало многопоточного выполнения
    print("Запуск потоков")
    start_time = time.time()
    
    urls = load_urls()
    num_threads = 8
    chunks = divide_into_chunks(urls, num_threads)
    threads = []
    
    # Инициализация и запуск потоков в адресном пространстве одного процесса ОС
    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=thread_worker, args=(chunk,), name=str(i+1))
        threads.append(t)
        t.start()
        
    # Блокировка основного потока исполнения до завершения работы всех дочерних
    for t in threads:
        t.join()
        
    timespent = time.time() - start_time
    print(f"Threading - завершено за {timespent:.4f} сек\n")
    return timespent
```


### Время выполнения

## Общая оценка

Все три режима (threading, multiprocessing, asyncio) успешно выполнились, данные сохранились в БД. Результаты выглядят логично для такой задачи.

### 1. Все три подхода работают

| Подход | Время | Комментарий |
|---|---|---|
| **Asyncio** | **7.31 сек** | Самый быстрый |
| Multiprocessing | 55.50 сек | ~7.6× медленнее asyncio |
| Threading | 58.01 сек | ~7.9× медленнее asyncio |

**Вывод:** asyncio **значительно быстрее** для I/O-bound задач (сетевые запросы).

### 2. Почему multiprocessing и threading такие медленные

Парсер работает с сетевыми запросами, постоянно происходит ожидание ответа от сайтов. Для таких задач:

- **Asyncio** идеален — один поток, тысячи одновременных запросов через event loop.
- **Threading** ограничен **GIL** и накладными расходами на переключение потоков. Плюс `requests` — синхронная библиотека, каждый поток блокируется на `requests.get()`.
- **Multiprocessing** ещё медленнее — **накладные расходы на форк процессов** в Windows (`spawn`) очень велики: каждый процесс заново импортирует модули, создаёт свой SQLAlchemy engine, подключается к БД.


### Положительные моменты

1. **Asyncio в ~8 раз быстрее** threading и multiprocessing — классический результат для I/O-bound задач.
2. **Multiprocessing не дал выигрыша** — из-за накладных расходов на форк процессов в Windows.
3. **Все три подхода корректно сохранили данные** в PostgreSQL через SQLAlchemy.
4. **Race condition** обрабатывается через `try/except IntegrityError` с ретраями.
5. **Технический пользователь `parser`** создаётся автоматически, все данные привязаны к нему.


### Вывод

Для задачи парсинга веб-страниц (I/O-bound) **асинхронный подход на базе `asyncio` + `aiohttp` показал наилучшую производительность** — 7.3 сек против 55–58 сек у threading и multiprocessing. Это объясняется тем, что `asyncio` использует один поток и event loop для обработки тысяч одновременных соединений, тогда как threading ограничен GIL, а multiprocessing тратит ресурсы на создание изолированных процессов и повторную инициализацию подключения к БД. Для CPU-bound задач (например, парсинг больших HTML-документов) multiprocessing мог бы показать лучший результат.
Это ожидаемый результат, поэтому в реальных проектах для I/O-bound задач выбирают asyncio, для CPU-bound — multiprocessing.