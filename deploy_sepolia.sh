#!/bin/bash

echo "============================================================"
echo "Sepolia Deployment Script"
echo "============================================================"
echo ""

cd contracts

echo "Step 1: Checking environment..."
npx ts-node scripts/check-env.ts
if [ $? -ne 0 ]; then
    echo ""
    echo "Environment check failed. Please fix the errors above."
    exit 1
fi

echo ""
echo "============================================================"
echo "Step 2: Deploying contracts to Sepolia..."
echo "============================================================"
echo ""

npx hardhat run scripts/deploy-sepolia.ts --network sepolia
if [ $? -ne 0 ]; then
    echo ""
    echo "Deployment failed!"
    exit 1
fi

echo ""
echo "============================================================"
echo "Step 3: Running Python test..."
echo "============================================================"
echo ""

cd ..
python -m backend.test_sepolia_deployment
if [ $? -ne 0 ]; then
    echo ""
    echo "Test failed!"
    exit 1
fi

echo ""
echo "============================================================"
echo "Deployment Complete!"
echo "============================================================"
echo ""
echo "Check backend/sepolia_deployment.json for deployment details."
echo ""
