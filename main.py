import itertools, asyncio
from fetchers.smartstore import smartstore_client
from invoices.builder import build_invoices
 ss, cp = await asyncio.gather(
        smartstore_client.fetch_orders(), 
        cp_fetch()
    )
from exporter.csv_exporter import save_csv
from notifier.kakao import send_file_link     # TODO: 링크 함수 완성
from dotenv import load_dotenv
load_dotenv()               # .env 값을 환경변수로 주입

async def run():
    ss, cp = await asyncio.gather(ss_fetch(), cp_fetch())
    orders = ss + cp
    invoices = list(itertools.chain.from_iterable(build_invoices(o) for o in orders))
    csv_path = save_csv(invoices)
    # csv_path를 S3/Render static에 업로드 → URL
    # send_file_link(url)

if __name__ == '__main__':
    asyncio.run(run())
