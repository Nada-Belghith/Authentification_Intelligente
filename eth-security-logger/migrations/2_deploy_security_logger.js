const SecurityLogger = artifacts.require("SecurityLogger");

module.exports = function (deployer, network, accounts) {
  // Use the first account from Ganache as deployer and set an explicit gas limit.
  const deployerAddress = accounts && accounts.length ? accounts[0] : undefined;
  const deployOptions = {};
  if (deployerAddress) deployOptions.from = deployerAddress;
  // set gas to network block gas limit (safe default)
  deployOptions.gas = 6721975;

  return deployer.deploy(SecurityLogger, { ...deployOptions });
};