import requests


def main():
    url = "http://18.180.162.113:9191/inst/getInst"
    params = {"symbol": "0939.HK", "duration": "1385"}
    r = requests.get(url, params=params, timeout=15, headers={"accept": "application/json"})
    print("status:", r.status_code)
    txt = r.text
    print("text_head:", txt[:600])
    try:
        j = r.json()
        print("type:", type(j).__name__)
        if isinstance(j, dict):
            print("keys:", list(j.keys())[:20])
            print("sample:", j)
        elif isinstance(j, list):
            print("list_len:", len(j))
            if j:
                print("first:", j[0])
    except Exception as e:
        print("json-parse-error:", e)


if __name__ == "__main__":
    main()


