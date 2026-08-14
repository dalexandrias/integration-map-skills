#!/bin/bash
# sobe a remessa diaria para o SFTP do banco conveniado
sftp -b - remessa@sftp.bancoconveniado.com.br <<CMD
put /opt/app/saida/REM_$(date +%Y%m%d).txt /entrada/
CMD
