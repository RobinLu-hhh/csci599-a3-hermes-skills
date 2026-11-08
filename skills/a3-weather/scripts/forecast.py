"""Standard-library Open-Meteo reader, without course accounts or state.
Source: https://open-meteo.com/en/docs — Forecast API; data CC BY 4.0.
AI attribution: initial draft and validation/CLI refinement generated with Codex.
"""
import json
import math
import ssl
import sys
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_BYTES = 100000
DOCS = 'README.md#故障排查'


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('source_response_invalid')
    return value


def forecast(latitude=34.05, longitude=-118.24, zone='America/Los_Angeles', opener=urlopen, *, now=None):
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        raise ValueError('invalid_weather_location')
    if not -90 <= float(latitude) <= 90 or not -180 <= float(longitude) <= 180:
        raise ValueError('invalid_weather_location')
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError('invalid_clock')
    today = current.astimezone(ZoneInfo(zone)).date()
    dates = [today.isoformat(), (today + timedelta(days=1)).isoformat()]
    params = {'latitude': float(latitude), 'longitude': float(longitude), 'timezone': zone,
              'start_date': dates[0], 'end_date': dates[1],
              'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max',
              'temperature_unit': 'celsius'}
    request = Request('https://api.open-meteo.com/v1/forecast?' + urlencode(params),
                      headers={'User-Agent': 'A3-weather/1.0'})
    with opener(request, timeout=15) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('source_response_invalid')
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get('daily'), dict):
        raise ValueError('source_response_invalid')
    daily = value['daily']
    fields = ('time', 'temperature_2m_max', 'temperature_2m_min', 'precipitation_probability_max')
    if any(not isinstance(daily.get(key), list) or len(daily[key]) != 2 for key in fields):
        raise ValueError('source_response_invalid')
    if daily['time'] != dates:
        raise ValueError('source_date_mismatch')
    days = []
    for i, date in enumerate(dates):
        high, low, rain = [number(daily[key][i]) for key in fields[1:]]
        if high < low or not 0 <= rain <= 100:
            raise ValueError('source_response_invalid')
        days.append({'date': date, 'highC': high, 'lowC': low, 'rainProbabilityPct': rain})
    return {'days': days, 'timezone': zone, 'source': 'https://open-meteo.com/',
            'attribution': 'Weather data by Open-Meteo (CC BY 4.0)',
            'fetchedAt': datetime.now(timezone.utc).isoformat(), 'stale': False, 'cached': False}


def failure(code, cause, fix):
    return {'error': {'code': code, 'problem': '无法取得可核对的天气预报。',
                      'cause': cause, 'fix': fix, 'docs': DOCS}}


def report(value):
    lines = ['日期 | 最高°C | 最低°C | 降雨概率%', '--- | --- | --- | ---']
    for day in value['days']:
        lines.append(f"{day['date']} | {day['highC']} | {day['lowC']} | {day['rainProbabilityPct']}%")
    return '\n'.join(lines + ['timezone: '+value['timezone'], 'fetchedAt: '+value['fetchedAt'],
                             '来源: '+value['source'], value['attribution']])


def main():
    try:
        value = forecast()
        value['report'] = report(value)
    except ZoneInfoNotFoundError:
        value = failure('timezone_unavailable', '缺少IANA时区数据', '安装操作系统时区数据库或Python tzdata后重试。')
    except HTTPError as exc:
        value = failure('source_rate_limited' if exc.code == 429 else 'source_unavailable',
                        'HTTP ' + str(exc.code), '稍后重试；不要把失败或旧数据当成当前天气。')
    except (URLError, TimeoutError, OSError, ssl.SSLError):
        value = failure('source_unavailable', '网络、TLS或超时', '检查网络及TLS CA数据，确认可访问api.open-meteo.com后重试。')
    except (ValueError, TypeError, UnicodeError):
        value = failure('source_response_invalid', '响应格式、日期或数值无效', '保留错误代码并稍后重试；不要生成替代天气数值。')
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))
    return 3 if 'error' in value else 0


if __name__ == '__main__':
    sys.exit(main())
