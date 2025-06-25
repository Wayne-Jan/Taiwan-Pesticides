# 臺灣農藥登記清單

本專案改編自原始儲存庫，提供臺灣農藥登記資料的自動化擷取工具。

## 致謝
本專案強烈基於 [Raingel](https://github.com/Raingel) 的 [Pesticides 專案](https://github.com/Raingel/Pesticides/)。我們在原始概念和代碼架構的基礎上進行了重大改進和功能擴展。感謝原作者的貢獻。

## 資料來源

本系統整合兩個政府網站的資料：

### 1. [**植物保護資訊系統**](https://otserv2.acri.gov.tw/PPM/) (農業部農業藥物試驗所)
- **功能**：提供作物病蟲害防治的農藥使用建議
- **擷取資料**：
  - 各作物分類的農藥使用資料 (`/data/usage/{作物名稱}_pesticide_data.csv`)
  - 包含：藥劑名稱、作用機制、稀釋倍數、施藥方法、注意事項等

### 2. [**農藥資訊服務網**](https://pesticide.baphiq.gov.tw/information/Query/Pesticide) (行政院農業委員會動植物防疫檢疫局)
- **功能**：提供農藥登記與管理的法規資訊
- **擷取資料**：
  - 臺灣現有藥劑列表及其使用範圍 (`/data/pesticides.csv`)
  - 各藥劑之成品製劑(許可證) (`/data/registered.csv`)
  - 各成品製劑之外觀標示圖檔 (`/label_img/` 及 `/data/images/`)
  - 個別農藥詳細註冊資料 (`/data/pesticides/{農藥代碼}/`)

## 使用方法

### 環境設置
```bash
# 激活虛擬環境
source venv/bin/activate
# 或使用
source pesticides_venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 資料擷取

#### 方法一：新版擷取器 (推薦)
適用於獲取各作物分類的詳細農藥使用資料：

```bash
# 測試模式 - 處理前10個新作物 (自動跳過已存在檔案)
python new_fetcher.py

# 處理所有新作物 (自動跳過已存在檔案)
python new_fetcher.py --full

# 強制重新下載所有作物 (忽略現有檔案)
python new_fetcher.py --full --force

# 自訂輸出檔名
python new_fetcher.py --full -o custom_data.csv

# 限制處理數量
python new_fetcher.py -l 50 -o sample_data.csv
```

**輸出**：每個作物分類會產生個別的CSV檔案，存放在 `data/usage/` 目錄
- 檔名格式：`{作物名稱}_{base_filename}`
- 實際案例：`data/usage/水稻稻種消毒_pesticide_data.csv`
- 特殊字符會被替換為底線：`data/usage/水稻秧苗徒長病_稻公_馬鹿苗病__pesticide_data.csv`

#### 方法二：原版擷取器
適用於獲取整體農藥清單和標示圖片：

```bash
# 下載化學藥劑清單
python fetcher.py -a chemicals

# 下載產品標示清單
python fetcher.py -a label

# 下載標示圖片 (需先執行 label 動作)
python fetcher.py -a label_img

# 下載指定範圍的標示圖片
python fetcher.py -a label_img -s 0 -e 100
```

#### 方法三：台灣法規資料擷取器 (新增)
適用於獲取農藥註冊和法規資料：

```bash
# 下載所有資料 (農藥清單 + 註冊資料)
python taiwan_fetcher.py

# 僅下載農藥清單
python taiwan_fetcher.py -a pesticides

# 僅下載註冊資料
python taiwan_fetcher.py -a registrations

# 限制註冊資料頁數 (測試用)
python taiwan_fetcher.py -a registrations --max-pages 5

# 自訂輸出檔名
python taiwan_fetcher.py -o my_taiwan_data
```

### 參數說明

#### new_fetcher.py 參數
- `-o, --output`: 輸出CSV檔名 (預設: `pesticide_data.csv`)
- `-l, --limit`: 限制處理的作物數量 (預設: 10)
- `--full`: 處理所有作物 (忽略 limit 參數)
- `--force`: 強制重新下載所有作物 (忽略現有檔案)

#### fetcher.py 參數
- `-a, --action`: 動作類型
  - `chemicals`: 下載化學藥劑清單
  - `label`: 下載產品標示清單
  - `label_img`: 下載標示圖片
- `-s, --regtnostart`: 起始索引 (僅用於 label_img)
- `-e, --regtnoend`: 結束索引 (僅用於 label_img)

#### taiwan_fetcher.py 參數
- `-a, --action`: 資料類型
  - `pesticides`: 僅下載農藥清單
  - `registrations`: 僅下載註冊資料
  - `both`: 下載所有資料 (預設)
- `-o, --output`: 輸出檔案基礎名稱 (預設: `taiwan_pesticide`)
- `--max-pages`: 限制註冊資料頁數 (預設: 全部)
- `--page-size`: 每頁記錄數 (預設: 100)

### 完整工作流程
```bash
# 1. 激活環境
source venv/bin/activate

# 2. 獲取作物分類資料 (新版)
python new_fetcher.py --full

# 3. 獲取整體藥劑清單 (原版)
python fetcher.py -a chemicals
python fetcher.py -a label

# 4. 獲取台灣法規資料 (新增)
python taiwan_fetcher.py

# 5. 下載標示圖片 (原版)
python fetcher.py -a label_img
```

### 輸出檔案結構
```
data/                           # 農藥資料庫 (依類型分類)
├── usage/                      # 作物使用資料 (new_fetcher.py)
│   ├── 水稻稻種消毒_pesticide_data.csv
│   ├── 水稻育苗箱秧苗立枯病_pesticide_data.csv
│   ├── 水稻秧苗徒長病_稻公_馬鹿苗病__pesticide_data.csv
│   ├── 玉米螟_pesticide_data.csv
│   ├── 落花生夜蛾類_甜菜夜蛾_斜紋夜蛾__pesticide_data.csv
│   ├── 豆科豆菜類夜蛾類_pesticide_data.csv
│   └── ... (共2877個作物分類，378+個檔案)
├── products/                   # 產品清單資料 (fetcher.py)
│   ├── pesticides.csv          # 整體農藥清單
│   ├── registered.csv          # 產品註冊清單
│   ├── pesticides_2025-06-24.csv  # 備份檔案
│   └── registered_2025-06-24.csv  # 備份檔案
└── regulatory/                 # 法規資料 (taiwan_fetcher.py)
    ├── taiwan_pesticide_list.csv        # 台灣農藥清單 (792筆)
    └── taiwan_pesticide_registrations.csv # 台灣註冊資料 (12976筆)

label_img/                      # 產品標示圖片 (fetcher.py)
├── image1.jpg                  
├── image2.jpg                  
└── ...
```

### CSV檔案內容結構
每個作物分類的CSV檔案包含以下欄位：
```
全選              # 選擇框
藥劑名稱           # 農藥名稱與濃度
作用機制代碼       # FRAC代碼與作用機制說明
浸藥時間          # 處理時間 (如: 24小時、4～12小時)
稀釋倍數(倍)      # 稀釋比例 (如: 2000倍、1000倍)
施藥方法          # 使用方式說明
注意事項          # 使用注意事項
作物名稱          # 作物分類名稱
資料來源URL       # 政府網站來源連結
擷取時間          # 資料擷取時間戳記
```

### 資料類型對比

| 工具 | 用途 | 資料來源 | 主要內容 |
|---------|-----|-------|---------|  
| **new_fetcher.py** | 作物使用指南 | 植物保護資訊系統 | 使用方法、稀釋倍數、施藥時期 |
| **split_pesticides_with_images.py** | 農藥詳細資料 | 農藥登記管理系統 | 註冊資料、標示圖片、製造商資訊 |

### 實際資料範例

#### 作物使用資料 (new_fetcher.py)
`data/usage/水稻稻種消毒_pesticide_data.csv`:
```csv
藥劑名稱,作用機制代碼,浸藥時間,稀釋倍數(倍),施藥方法,注意事項
250 g/L (25% w/v) 得克利 水基乳劑,FRAC 3;G1 系統性,24小時,2000,稻種直接消毒24小時後再浸水催芽,
50% 免賴得 可溼性粉劑,FRAC 1;B1 系統性,浸藥4～12小時,1000,稻種預先浸水催芽至萌芽時浸漬,藥液調配後24小時內可連續使用三次
```

#### 農藥個別資料 (split_pesticides_with_images.py)
`data/pesticides/T027____TRIFLOXYSTROBIN/T027____TRIFLOXYSTROBIN.csv`:
```csv
許可證字號,普通名稱,廠牌名稱,劑型,含量,製造商,有效期限,標示圖片,使用範圍URL
農藥製字第05877號,三氟敏,富米熊,水懸劑,500g/L,全國農業資材行,2026-10-22,/data/images/三氟敏/image1.jpg | 2024-01-15,https://...
農藥進字第02903號,三氟敏,拿赶,水懸劑,500g/L,拜耳作物科學公司,2025-10-17,/data/images/三氟敏/image2.jpg | 2024-01-15,https://...
```

### 主要功能特色

1. **智慧型重複偵測** (new_fetcher.py)
   - 自動跳過已下載的作物檔案
   - 支援增量更新，避免重複下載
   - 可使用 `--force` 強制更新所有資料

2. **圖片下載與管理** (split_pesticides_with_images.py)
   - 自動從農藥登記管理系統下載標示圖片
   - 依農藥名稱分類存放
   - 記錄圖片路徑與下載時間

3. **資料整理與分類**
   - 作物使用資料：依作物分類個別存檔
   - 農藥資料：依農藥代碼分類存檔
   - 圖片資料：依農藥名稱分類存放
# 關於農藥登記
臺灣的農藥登記屬於**正面表列**，每一藥劑都會有特定之**使用範圍**。換句話說，於**特定作物上僅得使用特定已登記之藥劑**，其餘未登記者皆不可使用。相關資訊可於[**「登記農藥查詢」**](https://pesticide.baphiq.gov.tw/information/Query/Pesticide "**「登記農藥查詢」**")系統上查詢。查詢水稻稻熱病用藥之範例如下表：


|普通名稱|含量|劑型代碼|每公頃每次用量|稀釋倍數|使用時期|施藥間隔|施用次數|安全採收期|施藥方法|注意事項|說明|核准日期|原始登記廠商名稱|
| ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ |
|三賽唑|75.000(%) (w/w)|WP|葉:0.33公斤;穗:0.4公斤|30L/公頃水量|抽穗前7天施藥1次即可|-|-|25|使用共力牌動力噴霧機第1段速度，於清晨無風時噴撒|稻熱病低容量劑防治，葉稻熱病之施藥時間及次數按照一般方法。穗稻熱病於抽穗前7天施藥1次即可。||||


而實際施用上，每一藥劑常常有不同廠商生產之**成品製劑**。此時則可至[**「許可證查詢」**](https://pesticide.baphiq.gov.tw/information/Query/Register "**「許可證查詢」**")系統上查詢。系統上同時會有該成品製劑之外標示，範例如下表：

|許可證號碼|普通名稱|廠牌名稱|劑型|含量|UP|混合|廠商名稱|國外原製造廠|有效日期|備註|標示|使用範圍|
| ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ |
|農藥製 03877|三賽唑|雙冬穩|WP 可溼性粉劑|75.000 (%) (w/w)|||日農科技股份有限公司||115-10-22||[標示](https://pesticide.baphiq.gov.tw/information/Query/RegisterViewMark/?regtid=10&regtno=03877 "標示")|[使用範圍](https://pesticide.baphiq.gov.tw/information/Query/Userange/?pestcd=F011&cidecd=WP%20%20&pescnt=75.000%20&compno=99657438&regtid=10&regtno=03877&newquery=true "使用範圍")|
|農藥製 04433|三賽唑|佳生|WP 可溼性粉劑|75.000 (%) (w/w)|||嘉農企業股份有限公司||112-10-17||[標示](https://pesticide.baphiq.gov.tw/information/Query/RegisterViewMark/?regtid=10&regtno=04433 "標示")|[使用範圍](https://pesticide.baphiq.gov.tw/information/Query/Userange/?pestcd=F011&cidecd=WP%20%20&pescnt=75.000%20&compno=99667762&regtid=10&regtno=04433&newquery=true "使用範圍")|




