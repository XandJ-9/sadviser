import aiohttp,asyncio
import re

headers={
  "Referer":'https://finance.sina.com.cn',
  "Content-Type": 'application/json'
}

# url="https://hq.sinajs.cn?list=nf_sz000627"
base_url="https://hq.sinajs.cn/list=sz300750,sh60000"

p = re.compile('\"(.*)\"')


async def main():
  async with aiohttp.ClientSession() as session:
    async with session.get(url=base_url, headers=headers) as response:
      # print(response.headers)
      res = await response.text(encoding='GB18030')
      print(res)
      info = p.findall(res)[0]
      if info:
        arr = info.split(',')
        name = arr[0]
        open_val = arr[2]
        high = arr[3]
        ow = arr[4]
        current_price = arr[8]
        pre_price = arr[10]
        print(f'名称: {name} \n开盘价：{open_val} \n最高价：{high} \n当前价：{current_price} \n昨日价：{pre_price}')




asyncio.run(main())