@echo off
echo ============================
echo IA-KPI - Limpeza de Historico Git
echo ============================

:: Verifica se está na pasta do projeto
cd /d "%~dp0"

:: Instala git-filter-repo, se necessário
echo.
echo Instalando git-filter-repo via pip...
pip install git-filter-repo

:: Remove os arquivos .db do histórico
echo.
echo Removendo arquivos .db do histórico do Git...
git filter-repo --path data/cliente_dados.db --path data/cliente_1.db --invert-paths

:: Força o push limpo para o GitHub
echo.
echo Enviando mudanças para o GitHub com git push --force...
git push origin --force

echo.
echo ✅ Limpeza concluída com sucesso!
pause
