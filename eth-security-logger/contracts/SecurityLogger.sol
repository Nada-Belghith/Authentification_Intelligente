// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SecurityLogger {
    struct SecurityLog {
        bytes32 logHash;
        string riskCode;
        uint256 timestamp;
        address sender;
    }

    SecurityLog[] public logHistory;
    event LogRecorded(bytes32 indexed logHash, string riskCode, uint256 timestamp);

    function recordLog(bytes32 _logHash, string memory _riskCode) public {
        logHistory.push(SecurityLog(
            _logHash,
            _riskCode,
            block.timestamp,
            msg.sender
        ));
        emit LogRecorded(_logHash, _riskCode, block.timestamp);
    }

    function getLogCount() public view returns (uint256) {
        return logHistory.length;
    }
}
