# 臺灣農藥登記清單

本系統之資料來源為 行政院農業委員會動植物防疫檢疫局 - [農藥資訊服務網](https://pesticide.aphia.gov.tw)
本系統提供工具從 行政院農業委員會動植物防疫檢疫局 - [農藥資訊服務網](https://pesticide.aphia.gov.tw)擷取臺灣現有藥劑列表及其使用範圍、各藥劑之成品製劑(許可證)以及各成品製劑之外觀標示圖檔

## 關於農藥登記

臺灣的農藥登記屬於**正面表列**，每一藥劑都會有特定之**使用範圍**。換句話說，於**特定作物上僅得使用特定已登記之藥劑**，其餘未登記者皆不可使用。相關資訊可於[**「登記農藥查詢」**](https://pesticide.aphia.gov.tw/information/Query/Pesticide "**「登記農藥查詢」**")系統上查詢。查詢水稻稻熱病用藥之範例如下表：

|普通名稱|含量|劑型代碼|每公頃每次用量|稀釋倍數|使用時期|施藥間隔|施用次數|安全採收期|施藥方法|注意事項|說明|核准日期|原始登記廠商名稱|
| ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ |
|三賽唑|75.000(%) (w/w)|WP|葉:0.33公斤;穗:0.4公斤|30L/公頃水量|抽穗前7天施藥1次即可|-|-|25|使用共力牌動力噴霧機第1段速度，於清晨無風時噴撒|稻熱病低容量劑防治，葉稻熱病之施藥時間及次數按照一般方法。穗稻熱病於抽穗前7天施藥1次即可。||||

而實際施用上，每一藥劑常常有不同廠商生產之**成品製劑**。此時則可至[**「許可證查詢」**](https://pesticide.aphia.gov.tw/information/Query/Register "**「許可證查詢」**")系統上查詢。系統上同時會有該成品製劑之外標示，範例如下表：

|許可證號碼|普通名稱|廠牌名稱|劑型|含量|UP|混合|廠商名稱|國外原製造廠|有效日期|備註|標示|使用範圍|
| ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ | ------------ |
|農藥製 03877|三賽唑|雙冬穩|WP 可溼性粉劑|75.000 (%) (w/w)|||日農科技股份有限公司||115-10-22||[標示](https://pesticide.aphia.gov.tw/information/Query/RegisterViewMark/?regtid=10&regtno=03877 "標示")|[使用範圍](https://pesticide.aphia.gov.tw/information/Query/Userange/?pestcd=F011&cidecd=WP%20%20&pescnt=75.000%20&compno=99657438&regtid=10&regtno=03877&newquery=true "使用範圍")|
|農藥製 04433|三賽唑|佳生|WP 可溼性粉劑|75.000 (%) (w/w)|||嘉農企業股份有限公司||112-10-17||[標示](https://pesticide.aphia.gov.tw/information/Query/RegisterViewMark/?regtid=10&regtno=04433 "標示")|[使用範圍](https://pesticide.aphia.gov.tw/information/Query/Userange/?pestcd=F011&cidecd=WP%20%20&pescnt=75.000%20&compno=99667762&regtid=10&regtno=04433&newquery=true "使用範圍")|

## 資料來源

本系統整合兩個政府網站的資料：

### 1. [**植物保護資訊系統**](https://otserv2.acri.gov.tw/PPM/) (農業部農業藥物試驗所)
- **功能**：提供作物病蟲害防治的農藥使用建議
- **擷取資料**：各作物分類的農藥使用資料，包含藥劑名稱、作用機制、稀釋倍數、施藥方法等

### 2. [**農藥資訊服務網**](https://pesticide.aphia.gov.tw) (農業部動植物防疫檢疫署)
- **功能**：提供農藥登記與管理的法規資訊
- **擷取資料**：農藥註冊資料、標示圖片、製造商資訊等

## 使用方法

### 環境設置
```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt
```

### 資料擷取

#### 方法一：作物農藥使用資料擷取器
獲取各作物分類的詳細農藥使用資料：

```bash
# 測試模式 - 處理前10個作物
python new_fetcher.py

# 處理所有作物
python new_fetcher.py --full

# 強制重新下載所有作物
python new_fetcher.py --full --force
```

#### 方法二：農藥資料分割與圖片下載器
處理農藥法規資料並下載標示圖片：

```bash
# 處理農藥資料並下載圖片
python split_pesticides_with_images.py

# 指定輸入檔案
python split_pesticides_with_images.py -i custom_input.csv
```

### 參數說明

#### new_fetcher.py 參數
- `-o, --output`: 輸出CSV檔名 (預設: `pesticide_data.csv`)
- `-l, --limit`: 限制處理的作物數量 (預設: 10)
- `--full`: 處理所有作物
- `--force`: 強制重新下載所有作物

#### split_pesticides_with_images.py 參數
- `-i, --input`: 輸入CSV檔案路徑 (預設: `data/regulatory/taiwan_comprehensive_combined.csv`)
- `-o, --output`: 輸出目錄路徑 (預設: `data`)

### 輸出檔案結構
```
data/
├── usage/          # 作物使用資料 (new_fetcher.py)
│   ├── 水稻稻種消毒_pesticide_data.csv
│   ├── 玉米螟_pesticide_data.csv
│   └── ...
├── pesticides/     # 個別農藥資料 (split_pesticides_with_images.py)
│   ├── A001____2_4_D/
│   │   └── A001____2_4_D.csv
│   └── ...
├── images/         # 農藥標示圖片
│   ├── 2_4_D/
│   │   ├── image1.jpg
│   │   └── ...
│   └── ...
└── regulatory/     # 法規資料
    ├── taiwan_comprehensive_combined.csv
    └── ...
```

## 致謝

本專案基於 [Raingel/Pesticides](https://github.com/Raingel/Pesticides/) 專案開發。