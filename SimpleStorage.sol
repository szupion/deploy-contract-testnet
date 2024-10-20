// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleStorage {
    string public name;

    // Constructor that sets the contract name
    constructor(string memory _name) {
        name = _name;
    }
}
