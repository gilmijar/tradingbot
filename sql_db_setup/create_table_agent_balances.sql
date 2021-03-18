CREATE TABLE `gdax`.`agent_balances` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `agent` VARCHAR(45) NOT NULL COMMENT 'investment strategy',
  `trade_id` VARCHAR(45) NOT NULL COMMENT 'trade identifier',
  `succesfull_flag` INT NOT NULL COMMENT '1 for true, 0 for false',
  `value` VARCHAR(45) NOT NULL COMMENT 'value of trade',
  `balances` VARCHAR(45) NOT NULL COMMENT 'cumulative balances of particular agent\nlatest shoul always show current agent balances',
  `timestamp` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`));