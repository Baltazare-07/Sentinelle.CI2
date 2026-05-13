const signer = new ethers.providers.Web3Provider(window.ethereum).getSigner();
const message = `Je signale ${type} à ${lat},${lng} le ${Date.now()}`;
const signature = await signer.signMessage(message);
// Envoie message + signature + adresse au backend