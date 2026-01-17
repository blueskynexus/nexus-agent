"""Pydantic schemas for Vianexus API responses"""

from pydantic import BaseModel, Field


class StockStatsData(BaseModel):
    """Response schema for CORE/STOCK_STATS_US dataset"""

    week_52_change: float = Field(alias="52weekChange")
    week_52_high: float = Field(alias="52weekHigh")
    week_52_high_date: str = Field(alias="52weekHighDate")
    week_52_low: float = Field(alias="52weekLow")
    week_52_low_date: str = Field(alias="52weekLowDate")
    avg_30_day_volume: int = Field(alias="avg30DayVolume")
    beta: float
    date: str
    day_200_moving_average: float = Field(alias="day200MovingAverage")
    day_50_moving_average: float = Field(alias="day50MovingAverage")
    eps_ttm: float = Field(alias="epsTtm")
    issuer_name: str = Field(alias="issuerName")
    mic: str
    pe_ratio_ttm: float = Field(alias="peRatioTtm")
    shares_outstanding: int = Field(alias="sharesOutstanding")
    symbol: str
    ytd_change: float | None = Field(alias="ytdChange", default=None)
    id: str
    key: str
    subkey: str
    updated: float

    class Config:
        populate_by_name = True


class VnxQuoteData(BaseModel):
    """Response schema for EDGE/VNX_QUOTE dataset"""

    vnx_symbol: str = Field(alias="vnxSymbol")
    vnx_bid_size: int = Field(alias="vnxBidSize")
    vnx_bid_price: float = Field(alias="vnxBidPrice")
    vnx_ask_size: int = Field(alias="vnxAskSize")
    vnx_ask_price: float = Field(alias="vnxAskPrice")
    vnx_price: float = Field(alias="vnxPrice")
    vnx_last_sale_price: float = Field(alias="vnxLastSalePrice")
    vnx_last_sale_size: int = Field(alias="vnxLastSaleSize")
    vnx_low_price: float = Field(alias="vnxLowPrice")
    vnx_high_price: float = Field(alias="vnxHighPrice")
    vnx_open_price: float = Field(alias="vnxOpenPrice")
    vnx_close_price: float = Field(alias="vnxClosePrice")
    vnx_volume: int = Field(alias="vnxVolume")
    vnx_timestamp: int = Field(alias="vnxTimestamp")
    vnx_market_percent: float = Field(alias="vnxMarketPercent")
    vnx_high_time: int = Field(alias="vnxHighTime")
    vnx_low_time: int = Field(alias="vnxLowTime")
    vnx_price_type: str = Field(alias="vnxPriceType")
    market_volume: int | None = Field(alias="MarketVolume", default=None)

    class Config:
        populate_by_name = True


class NewsArticle(BaseModel):
    """Response schema for CORE/NEWS dataset"""

    datetime: int  # Epoch milliseconds
    headline: str
    summary: str | None = None
    source: str | None = None
    provider: str
    symbol: str
    uuid: str
    url: str
    qm_url: str | None = Field(alias="qmUrl", default=None)
    image: str | None = None
    image_url: str | None = Field(alias="imageUrl", default=None)
    has_paywall: bool = Field(alias="hasPaywall", default=False)
    lang: str | None = None
    related: str | None = None

    class Config:
        populate_by_name = True


class QuoteData(BaseModel):
    """Response schema for CORE/QUOTE dataset"""

    symbol: str
    price: float = Field(alias="latestPrice")
    change: float = Field(alias="change")
    percent_change: float = Field(alias="changePercent")
    prev_close: float = Field(alias="previousClose")
    open: float | None = Field(alias="open", default=None)
    high: float | None = Field(alias="high", default=None)
    low: float | None = Field(alias="low", default=None)
    volume: int | None = Field(alias="volume", default=None)
    market_cap: int | None = Field(alias="marketCap", default=None)

    class Config:
        populate_by_name = True


class AdvancedDividends(BaseModel):
    """Response schema for advanced dividends dataset"""

    # Required fields
    symbol: str
    refid: str
    status: str

    # Optional fields
    adr_fee: int | None = Field(alias="adrFee", default=None)
    amount: float | None = None
    announce_date: str | None = Field(alias="announceDate", default=None)
    country_code: str | None = Field(alias="countryCode", default=None)
    coupon: float | None = None
    created: str | None = None
    currency: str | None = None
    declared_currency_cd: str | None = Field(alias="declaredCurrencyCD", default=None)
    declared_date: str | None = Field(alias="declaredDate", default=None)
    declared_gross_amount: float | None = Field(alias="declaredGrossAmount", default=None)
    description: str | None = None
    ex_date: str | None = Field(alias="exDate", default=None)
    figi: str | None = None
    fiscal_year_end_date: str | None = Field(alias="fiscalYearEndDate", default=None)
    flag: str | None = None
    frequency: str | None = None
    from_factor: float | None = Field(alias="fromFactor", default=None)
    fx_date: str | None = Field(alias="fxDate", default=None)
    gross_amount: float | None = Field(alias="grossAmount", default=None)
    installment_pay_date: str | None = Field(alias="installmentPayDate", default=None)
    is_approximate: bool | None = Field(alias="isApproximate", default=None)
    is_capital_gains: bool | None = Field(alias="isCapitalGains", default=None)
    is_dap: bool | None = Field(alias="isDAP", default=None)
    is_net_investment_income: bool | None = Field(alias="isNetInvestmentIncome", default=None)
    last_updated: str | None = Field(alias="lastUpdated", default=None)
    marker: str | None = None
    net_amount: float | None = Field(alias="netAmount", default=None)
    notes: str | None = None
    optional_election_date: str | None = Field(alias="optionalElectionDate", default=None)
    par_value: float | None = Field(alias="parValue", default=None)
    par_value_currency: str | None = Field(alias="parValueCurrency", default=None)
    payment_date: str | None = Field(alias="paymentDate", default=None)
    period_end_date: str | None = Field(alias="periodEndDate", default=None)
    record_date: str | None = Field(alias="recordDate", default=None)
    registration_date: str | None = Field(alias="registrationDate", default=None)
    second_ex_date: str | None = Field(alias="secondExDate", default=None)
    second_payment_date: str | None = Field(alias="secondPaymentDate", default=None)
    security_type: str | None = Field(alias="securityType", default=None)
    tax_rate: float | None = Field(alias="taxRate", default=None)
    to_date: str | None = Field(alias="toDate", default=None)
    to_factor: float | None = Field(alias="toFactor", default=None)
    un_adjusted_amount: float | None = Field(alias="unAdjustedAmount", default=None)

    class Config:
        populate_by_name = True
