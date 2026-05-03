const hre = require("hardhat");

async function main() {
    const Signalement = await hre.ethers.getContractFactory("Signalement");
    const signalement = await Signalement.deploy();
    await signalement.waitForDeployment();
    const address = await signalement.getAddress();
    console.log(`Signalement déployé à : ${address}`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});