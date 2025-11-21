import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re

USD_TO_RUB = 80.15
EUR_TO_RUB = 92.44

df = pd.read_csv('/Users/sergei/Downloads/_data.csv', low_memory=False)

def parse_price(x):
    s = str(x)
    nums = re.findall(r'\d+\.?\d*', s)
    if not nums: return np.nan
    if "USD" in s or "$" in s:
        rate = USD_TO_RUB
    elif "EUR" in s or "€" in s:
        rate = EUR_TO_RUB
    else:
        rate = 1
    return float(nums[0]) * rate

df['monthly_rent_rub'] = df['Цена'].apply(parse_price).round()

st.set_page_config(page_title="Анализ рынка аренды недвижимости", layout="wide", initial_sidebar_state="expanded")
st.title("Анализ рынка аренды в Москве")
st.subheader("Выберите график на панели слева")

with st.sidebar:
    st.write("## Полезные ссылки")
    st.page_link("http://www.cian.ru/", label="Циан", icon="🏡")
    st.page_link("https://elbrusboot.camp/datascience/", label="Эльбрус буткемп", icon="🏔")
    if st.button("🎈 Запустить шарики"):
        st.balloons()

st.sidebar.header("Выберите график")
choice = st.sidebar.selectbox("Построить график", [
    "Гистограмма цен",
    "Сегментация цен", 
    "Топ-10 станций метро", 
    "Цена / площадь", 
    "Цена / этаж",
    "ЦАО vs остальная Москва",
    "Цена vs минуты до метро",
    "Комнаты и ремонт"
])

# ============================================
# 1. Гистограмма цен
# ============================================
if choice == "Гистограмма цен":
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.histplot(df['monthly_rent_rub'].dropna(), bins=100, kde=True, color='darkblue', ax=ax)
    ax.set_xscale('log')
    ax.set_xticks([20_000, 30_000, 50_000, 80_000, 100_000, 200_000, 500_000, 1_000_000])
    ax.set_xticklabels(['20к','30к','50к','80к','100к','200к','500к','1М'])
    ax.set_title("Распределение стоимости аренды в Москве", fontsize=18, weight='bold')
    ax.set_xlabel("Цена аренды в месяц, ₽")
    ax.set_ylabel("Количество объявлений")
    median = df['monthly_rent_rub'].median()
    ax.axvline(median, color='red', linestyle='--', linewidth=2,
               label=f'Медиана = {median:,.0f} ₽')
    ax.legend()
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Выводы по распределению цен")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Медианная цена аренды", f"{median:,.0f} ₽")
    with col2:
        st.metric("75-й перцентиль", f"{df['monthly_rent_rub'].quantile(0.75):,.0f} ₽")
    with col3:
        st.metric("95-й перцентиль", f"{df['monthly_rent_rub'].quantile(0.95):,.0f} ₽")

    st.success("""
    **Зачем нужен этот график?**  
    Показывает, как распределяются цены на рынке. Видно, что основная масса предложений — до 100–120 тыс. ₽.  
    Хвост вправо — это элитная недвижимость. Логарифмическая шкала помогает увидеть структуру даже в дорогом сегменте.
    """)

# ============================================
# 2. Сегментация цен
# ============================================
elif choice == "Сегментация цен":
    bins = [0, 40000, 60000, 100000, 200000, df['monthly_rent_rub'].max()]
    labels = ['до 40 тыс', '40-60 тыс', '60-100 тыс', '100-200 тыс', 'более 200 тыс']
    df['price_group'] = pd.cut(df['monthly_rent_rub'], bins=bins, labels=labels)
    counts = df['price_group'].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(counts.index.astype(str), counts.values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1, 
                f'{int(bar.get_height())}', ha='center', va='bottom')
    ax.set_title('Распределение по ценовым категориям')
    ax.set_ylabel('Количество объявлений')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Анализ ценовых сегментов")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Самый массовый сегмент", f"{counts.idxmax()} ({counts.max():,} шт)")
    with col2:
        st.metric("Доля элитного сегмента (>200к)", 
                  f"{(counts['более 200 тыс']/len(df)*100):.1f}%")
    with col3:
        st.metric("Всего объявлений", f"{len(df):,}")

    st.success("""
    **Зачем нужен этот график?**  
    Делит рынок на понятные категории. Видно, где конкуренция максимальна (40–100 тыс.),  
    а где — премиум с низкой конкуренцией, но высокой маржой.
    """)

# ============================================
# 3. Топ-10 станций метро
# ============================================
elif choice == "Топ-10 станций метро":
    df['metro_station'] = df['Метро'].astype(str).str.split('(').str[0].str.strip()
    valid_metro = df[df['metro_station'].notna() & (df['metro_station'] != 'nan') & (df['metro_station'] != '')]
    top10_metro = valid_metro['metro_station'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    top10_metro.sort_values().plot(kind='barh', color='lightcoral', edgecolor='black', ax=ax)
    ax.set_title('Топ-10 станций метро по количеству объявлений')
    ax.set_xlabel('Количество объявлений')
    for i, v in enumerate(top10_metro.sort_values()):
        ax.text(v + 6, i, str(v), va='center', fontweight='bold')
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("География спроса")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Лидер по предложениям", top10_metro.index[0])
    with col2:
        st.metric("Всего станций в данных", df['metro_station'].nunique())

    st.success("""
    **Зачем нужен этот график?**  
    Показывает, где сосредоточено предложение — это и есть зоны максимального спроса.  
    Высокая концентрация = ликвидность, быстрый срок экспозиции, стабильная цена.
    """)

# ============================================
# 4. Цена / площадь
# ============================================
elif choice == "Цена / площадь":
    df['total_area'] = (df['Площадь, м2'].str.split('/').str[0]
                       .str.replace(',', '.').astype(float))
    df_normal = df[df['monthly_rent_rub'] <= 200000].copy()
    df_elite = df[df['monthly_rent_rub'] > 200000].copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df_normal['total_area'], df_normal['monthly_rent_rub'], alpha=0.3, color='green', label='Обычный рынок (99%)')
    ax.scatter(df_elite['total_area'], df_elite['monthly_rent_rub'], alpha=0.3, color='gold', s=50, label='Элитное жильё (1%)')
    ax.set_title('Зависимость цены от площади')
    ax.set_xlabel('Общая площадь, м²')
    ax.set_ylabel('Цена аренды, руб/месяц')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style='plain', axis='y')  # ИСПРАВЛЕНО: было обрезано
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Цена и метраж")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Средняя площадь", f"{df['total_area'].mean():.1f} м²")
    with col2:
        st.metric("Средняя цена за м²", f"{(df['monthly_rent_rub']/df['total_area']).mean():.0f} ₽")
    with col3:
        st.metric("Элитные объекты", f"{len(df_elite)} шт")

    st.success("""
    **Зачем нужен этот график?**  
    Подтверждает прямую зависимость: больше площадь — выше цена.  
    Золотые точки — элитный сегмент с премией за бренд, вид, ремонт и локацию.
    """)

# ============================================
# 5. Цена / этаж
# ============================================
elif choice == "Цена / этаж":
    df['floor'], df['total_floors'] = zip(*df['Дом'].astype(str).str.findall(r'\d+').apply(
        lambda x: (float(x[0]) if len(x)>0 else None, float(x[1]) if len(x)>1 else None)))
    df['first'] = df['floor'] == 1
    df['last'] = df['floor'] == df['total_floors']
    
    prices = [
        df[~df['first'] & ~df['last']]['monthly_rent_rub'].median(),
        df[df['first']]['monthly_rent_rub'].median(),
        df[df['last']]['monthly_rent_rub'].median()]
    labels = ['Средние этажи', 'Первый этаж', 'Последний этаж']
    
    fig, ax = plt.subplots(figsize=(10, 6.5))
    bars = ax.bar(labels, prices, color=['#4FC3F7', '#FF8A80', '#FFB74D'], 
                  edgecolor='black', linewidth=1.5, width=0.65)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.05,
                f'{int(height):,} ₽', ha='center', va='bottom',
                fontsize=13, fontweight='bold', color='#1a1a1a')
    
    ax.set_title('Влияние этажа на медианную цену аренды', 
                 fontsize=18, weight='bold', pad=30)
    ax.set_ylabel('Медианная цена, ₽')
    ax.grid(axis='y', alpha=0.3, linestyle='--', zorder=0)
    ax.set_ylim(0, max(prices) * 1.22) 
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Эффект этажа")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Средние этажи", f"{int(prices[0]):,} ₽")
    with col2:
        discount_first = ((prices[0] - prices[1]) / prices[0] * 100)
        st.metric("Первый этаж", f"{int(prices[1]):,} ₽", delta=f"-{discount_first:.1f}%")
    with col3:
        discount_last = ((prices[0] - prices[2]) / prices[0] * 100)
        st.metric("Последний этаж", f"{int(prices[2]):,} ₽", delta=f"-{discount_last:.1f}%")

    st.success("""
    **Зачем нужен этот график?**  
    • Первый и последний этажи — традиционно дешевле на 5–15%  
    • Исключения: пентхаусы (последний этаж в элитке) и дома с панорамным видом  
    • При прочих равных — берите средние этажи: цена выше, спрос стабильнее
    """)

# ============================================
# 6. ЦАО vs остальная Москва
# ============================================
elif choice == "ЦАО vs остальная Москва":
    cao_areas = ['Арбат','Басманный','Замоскворечье','Красносельский',
                 'Мещанский','Пресненский','Таганский','Тверской',
                 'Хамовники','Якиманка']
    df["is_cao"] = df["Адрес"].astype(str).str.contains("|".join(cao_areas), regex=True)
    
    m = df.groupby("is_cao")["monthly_rent_rub"].median()
    labels = ["Остальная Москва", "ЦАО"]
    
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(labels, m.values, color=["#95E1D3", "#FF6B6B"], edgecolor="black", linewidth=2.5, width=0.6)
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.08, 
                f'{int(height):,} ₽', 
                ha='center', va='bottom', fontsize=16, fontweight='bold', color='#2c3e50')

    ax.set_title("Медианная цена аренды: ЦАО vs остальная Москва", 
                 fontsize=18, weight='bold', pad=30)
    ax.set_ylabel("Медианная цена, ₽")
    ax.grid(axis="y", alpha=0.3, ls="--", zorder=0)
    ax.set_ylim(0, m.max() * 1.25)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)

    share_cao = df["is_cao"].mean()
    revenue_cao = df[df["is_cao"]]["monthly_rent_rub"].sum()
    revenue_total = df["monthly_rent_rub"].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Доля квартир в ЦАО", f"{share_cao * 100:.2f}%")
    with col2:
        st.metric("Доля выручки от ЦАО", f"{revenue_cao / revenue_total * 100:.1f}%")
    with col3:
        skew = (revenue_cao / revenue_total) / share_cao
        st.metric("Перекос выручки", f"{skew:.1f}×", delta=f"+{skew-1:.1f}× выше доли")

    st.success("""
    **Зачем нужен этот график?**  
    ЦАО — крошечная доля рынка по количеству объектов (обычно <1%),  
    но генерирует в разы больше выручки. Это классический премиум-сегмент:  
    мало объектов — огромная доходность на квадратный метр.
    """)

# ============================================
# 7. Цена vs минуты до метро
# ============================================
elif choice == "Цена vs минуты до метро":
    df['min_walk'] = df['Метро'].str.extract(r'(\d+)\s*мин.*?пешком', flags=re.I).astype(float)
    agg = (df[df['min_walk'] <= 30]
        .groupby('min_walk')['monthly_rent_rub']
        .median()
        .loc[lambda s: df['min_walk'].value_counts()[s.index] > 30]
        .rolling(5, center=True, min_periods=1).mean())

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(agg.index, agg, 'o-', color='#d62728', lw=7, ms=11, mfc='white', mew=3.5)
    ax.axvspan(0, 10, color='#ff3333', alpha=0.35, label='0–10 мин до метро')
    ax.set_ylim(30000, 70000)
    ax.set_yticks([30000,40000,50000,60000,70000])
    ax.set_yticklabels(['30к','40к','50к','60к','70к'])
    ax.set_title("Влияние расстояния до метро на цену аренды", fontsize=19, weight='bold', pad=30)
    ax.set_xlabel("Минут пешком до метро")
    ax.set_ylabel("Медианная цена аренды")
    ax.grid(alpha=0.25, axis='y', ls='--')
    ax.legend(fontsize=13)
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Стоимость времени")
    st.success("""
    **Зачем нужен этот график?**  
    Каждая минута пешком до метро снижает цену на 1 500–2 500 ₽ в месяц.  
    Объекты в 5–10 минутах пешком — золотая середина: цена уже заметно ниже, но метро рядом.
    """)

# ============================================
# 8. Комнаты и ремонт
# ============================================
elif choice == "Комнаты и ремонт":
    def rooms_cat(x):
        if pd.isna(x): return np.nan
        s = str(x).lower()
        if any(w in s for w in ['студия', 'своб', '0']): return 'Студия'
        n = re.search(r'\d+', s)
        return f"{n.group()}-комн" if n else np.nan
    
    rooms = df['Количество комнат'].apply(rooms_cat).value_counts().sort_values(ascending=False)
    
    repair_order = ['Дизайнерский', 'Евроремонт', 'Косметический', 'Без ремонта']
    df['Ремонт'] = df['Ремонт'].fillna('Без ремонта')
    repair = df['Ремонт'].value_counts().reindex(repair_order, fill_value=0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # По комнатам
    rooms.plot(kind='bar', ax=ax1, color='violet', edgecolor='black')
    ax1.set_title("По количеству комнат", fontsize=14, weight='bold', pad=15)
    ax1.set_ylabel("Объявлений")
    for i, v in enumerate(rooms):
        ax1.text(i, v + 120, f"{v:,}", ha='center', fontweight='bold')
    ax1.tick_params(axis='x', rotation=0)

    # По ремонту
    colors = ['#9b59b6', '#3498db', '#2ecc71', '#7f8c8d']
    repair.plot(kind='bar', ax=ax2, color=colors, edgecolor='black')
    ax2.set_title("По типу ремонта", fontsize=14, weight='bold', pad=15)
    ax2.set_ylabel("Объявлений")
    for i, v in enumerate(repair):
        ax2.text(i, v + 100, f"{v:,}", ha='center', fontweight='bold')
    ax2.tick_params(axis='x', rotation=0)

    plt.suptitle("Распределение объявлений по комнатности и ремонту", fontsize=18, weight='bold', y=1.05)
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("Структура предложения")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Самый популярный тип", f"{rooms.index[0]} ({rooms.iloc[0]:,} шт)")
    with col2:
        most_common_repair = repair.idxmax()
        st.metric("Чаще всего встречается ремонт", f"{most_common_repair} ({repair.max():,} шт)")

    st.success("""
    **Зачем нужен этот график?**  
    Показывает реальную структуру предложения:  
    • Доминируют 1- и 2-комнатные квартиры  
    • Косметический ремонт — абсолютный лидер (дешево и быстро)  
    • Евроремонт — второй по популярности  
    • Дизайнерский ремонт — редкость, но даёт серьёзную премию к цене аренды
    """)