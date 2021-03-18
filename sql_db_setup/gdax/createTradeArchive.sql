USE `gdax`;
DROP TABLE IF EXISTS `tradeArchive`;
CREATE TABLE IF NOT EXISTS `tradeArchive`(
	`ID` INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
	`ticker` VARCHAR(6) NOT NULL,
	`tradeId` INTEGER NOT NULL,
	`tradeType` TINYINT NOT NULL,
	`price` DECIMAL(12,4) UNSIGNED NOT NULL,
	`amount` DECIMAL(14,8) UNSIGNED NOT NULL,
	`tradeTimeStamp` INTEGER NOT NULL
    )
ROW_FORMAT=FIXED
ENGINE=ARIA;

CREATE UNIQUE INDEX iTradeId ON `tradeArchive`(`ticker`,`tradeId`);
CREATE INDEX iTradeTimeStamp ON `tradeArchive`(`tradeTimeStamp`);
CREATE INDEX iTradePrice ON `tradeArchive`(`price`);
