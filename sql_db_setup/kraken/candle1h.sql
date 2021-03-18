use kraken;
DROP TABLE IF EXISTS `candle1h`;

CREATE TABLE `candle1h` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ticker` varchar(12) NOT NULL,
  `timeMark` datetime NOT NULL COMMENT 'time of period start',
  `open` decimal(10,4) NOT NULL,
  `high` decimal(10,4) NOT NULL,
  `low` decimal(10,4) NOT NULL,
  `close` decimal(10,4) NOT NULL,
  `volume` decimal(12,8) NOT NULL,
  `tradeCount` int(11) NOT NULL,
  `sellVolume` decimal(12,8) NOT NULL,
  `sellCount` int(11) NOT NULL,
  `buyVolume` decimal(12,8) NOT NULL,
  `buyCount` int(11) NOT NULL,
  `openTime` datetime NOT NULL COMMENT 'time of first transaction',
  `closeTime` datetime NOT NULL COMMENT 'time of last transaction',
  `candleTime` datetime NOT NULL COMMENT 'time of candle creation',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `uiTimeMark` (`timeMark`)
) ENGINE=Aria AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 PACK_KEYS=0 PAGE_CHECKSUM=1 ROW_FORMAT=FIXED;
