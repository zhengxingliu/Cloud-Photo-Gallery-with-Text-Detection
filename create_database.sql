-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema ece1779_a2
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `ece1779_a2` ;

-- -----------------------------------------------------
-- Schema ece1779_a2
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `ece1779_a2` DEFAULT CHARACTER SET utf8 ;
USE `ece1779_a2` ;

-- -----------------------------------------------------
-- Table `ece1779_a2`.`user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_a2`.`user` ;

CREATE TABLE IF NOT EXISTS `ece1779_a2`.`user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(10) NOT NULL,
  `hash` BLOB NULL,
  `salt` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
  UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `ece1779_a2`.`photo`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_a2`.`photo` ;

CREATE TABLE IF NOT EXISTS `ece1779_a2`.`photo` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_photo_user_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_photo_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `ece1779_a2`.`user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `ece1779_a2`.`type`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_a2`.`type` ;

CREATE TABLE IF NOT EXISTS `ece1779_a2`.`type` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `label` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `ece1779_a2`.`transformation`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `ece1779_a2`.`transformation` ;

CREATE TABLE IF NOT EXISTS `ece1779_a2`.`transformation` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `filename` VARCHAR(128) NOT NULL,
  `type_id` INT NOT NULL,
  `photo_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_transformation_type1_idx` (`type_id` ASC) VISIBLE,
  INDEX `fk_transformation_photo1_idx` (`photo_id` ASC) VISIBLE,
  CONSTRAINT `fk_transformation_type1`
    FOREIGN KEY (`type_id`)
    REFERENCES `ece1779_a2`.`type` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_transformation_photo1`
    FOREIGN KEY (`photo_id`)
    REFERENCES `ece1779_a2`.`photo` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- Data for table `ece1779_a2`.`type`
-- -----------------------------------------------------
START TRANSACTION;
USE `ece1779_a2`;
INSERT INTO `ece1779_a2`.`type` (`id`, `label`) VALUES (1, 'original');
INSERT INTO `ece1779_a2`.`type` (`id`, `label`) VALUES (2, 'thumbnail');
INSERT INTO `ece1779_a2`.`type` (`id`, `label`) VALUES (3, 'textDetection');

COMMIT;

#CREATE USER 'ece1779' IDENTIFIED BY 'secret';
#commit;

GRANT ALL ON ece1779_a2.* TO 'ece1779';