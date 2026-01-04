@echo off
echo ============================================================
echo Sepolia Deployment Script
echo ============================================================
echo.

cd contracts

echo Step 1: Checking environment...
call npx ts-node scripts/check-env.ts
if %errorlevel% neq 0 (
    echo.
    echo Environment check failed. Please fix the errors above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Deploying contracts to Sepolia...
echo ============================================================
echo.

call npx hardhat run scripts/deploy-sepolia.ts --network sepolia
if %errorlevel% neq 0 (
    echo.
    echo Deployment failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 3: Running Python test...
echo ============================================================
echo.

cd ..
python -m backend.test_sepolia_deployment
if %errorlevel% neq 0 (
    echo.
    echo Test failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Deployment Complete!
echo ============================================================
echo.
echo Check backend/sepolia_deployment.json for deployment details.
echo.
pause
