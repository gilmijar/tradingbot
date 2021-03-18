CREATE TABLE IF NOT EXISTS `trade`(
	`ID` INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
	`tradeId` INTEGER NOT NULL,
	`tradeType` enum('sell', 'buy') NOT NULL COMMENT '0=sell or 1=buy',
	`price` DECIMAL(12,4) UNSIGNED NOT NULL,
	`amount` DECIMAL(14,8) UNSIGNED NOT NULL,
	`tradeTimeStamp` INTEGER NOT NULL
    )
ROW_FORMAT=FIXED
ENGINE=ARIA;

-- CREATE UNIQUE INDEX iTradeId ON trade(`tradeId`); 
-- we don't use trade id all that much, and index is taking up space
CREATE INDEX iTradeTimeStamp ON trade(`tradeTimeStamp`);
