# core/utils.py
import math

def map_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """
    위경도(WGS84)를 기상청 격자 좌표(NX, NY)로 변환한다.
    기상청 가이드의 Lambert Conformal Conic Projection 수식을 구현함.
    """
    RE = 6371.00877 # 지구 반경(km)
    GRID = 5.0      # 격자 간격(km)
    SLAT1 = 30.0    # 표준위도1(degree)
    SLAT2 = 60.0    # 표준위도2(degree)
    OLON = 126.0    # 기준점 경도(degree)
    OLAT = 38.0     # 기준점 위도(degree)
    XO = 42         # 기준점 X좌표(GRID)
    YO = 135        # 기준점 Y좌표(GRID)

    DEGRAD = math.pi / 180.0
    RADDEG = 180.0 / math.pi

    re = RE / GRID
    slat1 = SLAT1 * DEGRAD
    slat2 = SLAT2 * DEGRAD
    olon = OLON * DEGRAD
    olat = OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = ra * math.sin(theta) + XO
    y = ro - ra * math.cos(theta) + YO

    return int(x + 1.5), int(y + 1.5)

# 테스트 코드 (서울: 37.5665, 126.9780 -> 약 60, 127 근처)
if __name__ == "__main__":
    nx, ny = map_to_grid(37.5665, 126.9780)
    print(f"서울 -> NX: {nx}, NY: {ny}")
