-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema enade_dw
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema enade_dw
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `enade_dw` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `enade_dw` ;

-- -----------------------------------------------------
-- Table `enade_dw`.`dim_avaliacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `enade_dw`.`dim_avaliacao` (
  `sk_avaliacao` INT NOT NULL AUTO_INCREMENT,
  `id_avaliacao` INT NOT NULL DEFAULT 0,
  `grau_dificuldade_prova_formacao_geral` VARCHAR(25) NULL DEFAULT NULL,
  `grau_dificuldade_prova_componente_especifico` VARCHAR(25) NULL DEFAULT NULL,
  `avaliacao_da_relacao_extensao_tempo_prova` VARCHAR(45) NULL DEFAULT NULL,
  `avaliacao_enunciados_componente_especifico` VARCHAR(45) NULL DEFAULT NULL,
  `avaliacao_enunciados_formacao_geral` VARCHAR(45) NULL DEFAULT NULL,
  `tempo_de_prova` VARCHAR(45) NULL DEFAULT NULL,
  `avaliacao_equipamentos_curso` VARCHAR(25) NULL DEFAULT NULL,
  `avaliacao_ambiente_curso` VARCHAR(25) NULL DEFAULT NULL,
  `date_from` TIMESTAMP NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NULL DEFAULT '1',
  PRIMARY KEY (`sk_avaliacao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `enade_dw`.`dim_curso`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `enade_dw`.`dim_curso` (
  `sk_curso` INT NOT NULL AUTO_INCREMENT,
  `id_curso` INT NOT NULL DEFAULT 0,
  `nome_curso` VARCHAR(55) NULL DEFAULT NULL,
  `nome_municipio` VARCHAR(100) NULL DEFAULT NULL,
  `uf` CHAR(2) NULL DEFAULT NULL,
  `nome_estado` VARCHAR(45) NULL DEFAULT NULL,
  `nome_regiao` VARCHAR(45) NULL DEFAULT NULL,
  `modalidade_graduacao` VARCHAR(15) NULL DEFAULT NULL,
  `turno_graduacao` VARCHAR(50) NULL DEFAULT NULL,
  `categoria_administrativa` VARCHAR(45) NULL DEFAULT NULL,
  `date_from` TIMESTAMP NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NULL DEFAULT '1',
  PRIMARY KEY (`sk_curso`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `enade_dw`.`dim_estudante`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `enade_dw`.`dim_estudante` (
  `sk_estudante` INT NOT NULL AUTO_INCREMENT,
  `id_estudante` INT NOT NULL DEFAULT 0,
  `sexo` CHAR(1) NULL DEFAULT NULL,
  `idade` INT NULL DEFAULT NULL,
  `cor_raca` VARCHAR(20) NULL DEFAULT NULL,
  `ano_fim_ensino_medio` INT NULL DEFAULT NULL,
  `ano_ingresso_graduacao` INT NULL DEFAULT NULL,
  `tipo_escola_ensino_medio` VARCHAR(40) NULL DEFAULT NULL,
  `primeira_geracao` VARCHAR(20) NULL DEFAULT NULL,
  `escolaridade_pai` VARCHAR(35) NULL DEFAULT NULL,
  `escolaridade_mae` VARCHAR(35) NULL DEFAULT NULL,
  `motivacao_curso` VARCHAR(40) NULL DEFAULT NULL,
  `renda_familiar` VARCHAR(35) NULL DEFAULT NULL,
  `horas_trabalho` VARCHAR(40) NULL DEFAULT NULL,
  `cotas` VARCHAR(80) NULL DEFAULT NULL,
  `date_from` TIMESTAMP NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NULL DEFAULT '1',
  PRIMARY KEY (`sk_estudante`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `enade_dw`.`dim_tempo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `enade_dw`.`dim_tempo` (
  `sk_tempo` INT NOT NULL AUTO_INCREMENT,
  `id_tempo` INT NOT NULL DEFAULT 0,
  `ano_enade` INT NOT NULL,
  `data_aplicacao_prova` DATE NULL,
  `ano_extenso` VARCHAR(45) NULL DEFAULT NULL,
  `decada` INT NULL DEFAULT NULL,
  `decada_extenso` VARCHAR(45) NULL,
  `ciclo` INT NULL DEFAULT NULL,
  `ano_relativo_ciclo` INT NULL,
  `flag_ultimo_enade` TINYINT NULL,
  `edicao_anterior` INT NULL,
  `date_from` TIMESTAMP NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL DEFAULT NULL,
  `version` INT NULL DEFAULT '1',
  PRIMARY KEY (`sk_tempo`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `enade_dw`.`fato_enade`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `enade_dw`.`fato_enade` (
  `sk_tempo` INT NOT NULL,
  `sk_curso` INT NOT NULL,
  `sk_avaliacao` INT NOT NULL,
  `sk_estudante` INT NOT NULL,
  `nota_geral` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_formacao_geral` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_parte_objetiva_formacao_geral` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_parte_discursiva_formacao_geral` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_componente_especifico` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_parte_objetiva_componente_especifico` DECIMAL(5,2) NULL DEFAULT NULL,
  `nota_parte_discursiva_componente_especifico` DECIMAL(5,2) NULL DEFAULT NULL,
  PRIMARY KEY (`sk_tempo`, `sk_curso`, `sk_avaliacao`, `sk_estudante`),
  INDEX `fk_fato_enade_dim_estudante_idx` (`sk_estudante` ASC) VISIBLE,
  INDEX `fk_fato_enade_dim_curso1_idx` (`sk_curso` ASC) VISIBLE,
  INDEX `fk_fato_enade_dim_avaliacao1_idx` (`sk_avaliacao` ASC) VISIBLE,
  CONSTRAINT `fk_fato_enade_dim_avaliacao1`
    FOREIGN KEY (`sk_avaliacao`)
    REFERENCES `enade_dw`.`dim_avaliacao` (`sk_avaliacao`),
  CONSTRAINT `fk_fato_enade_dim_curso1`
    FOREIGN KEY (`sk_curso`)
    REFERENCES `enade_dw`.`dim_curso` (`sk_curso`),
  CONSTRAINT `fk_fato_enade_dim_estudante`
    FOREIGN KEY (`sk_estudante`)
    REFERENCES `enade_dw`.`dim_estudante` (`sk_estudante`),
  CONSTRAINT `fk_fato_enade_dim_tempo1`
    FOREIGN KEY (`sk_tempo`)
    REFERENCES `enade_dw`.`dim_tempo` (`sk_tempo`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
