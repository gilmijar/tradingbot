-- create table `orderbook`
-- row_format is fixed for speed, size, and better maintenance
DROP TABLE IF EXISTS `orderbook`;
CREATE TABLE IF NOT EXISTS `orderbook` (
    `orderTimeStamp` int(11) NOT NULL,
    `step` smallint(4) NOT NULL COMMENT 'negative for ask, positive bid',
    `price` decimal(12,4) unsigned NOT NULL,
    `amount` decimal(14,8) unsigned NOT NULL,
    PRIMARY KEY (`orderTimeStamp`,`step`)
)
ROW_FORMAT=FIXED
ENGINE=ARIA;
-- CREATE INDEX iPrice ON orderbook(`price`);
