// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract Source is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    mapping(address => bool) public approved;
    address[] public tokens;

    event Deposit(address indexed token, address indexed recipient, uint256 amount);
    event Withdrawal(address indexed token, address indexed recipient, uint256 amount);
    event Registration(address indexed token);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    function deposit(address _token, address _recipient, uint256 _amount) public {
        // YOUR CODE HERE
        require(approved[_token] == true, "Underlying token not registered");
        IERC20 underlyingToken = IERC20(_token);
        require(underlyingToken.transferFrom(msg.sender, address(this), _amount), "Token transfer failed");
        emit Deposit(_token, _recipient, _amount);
    }

    function withdraw(address _token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        // YOUR CODE HERE
        require(approved[_token] == true, "Underlying token not registered");
        IERC20 underlyingToken = IERC20(_token);
        require(underlyingToken.transfer(_recipient, _amount), "Token transfer failed");
        emit Withdrawal(_token, _recipient, _amount);
    }

    function registerToken(address _token) public onlyRole(ADMIN_ROLE) {
        // YOUR CODE HERE
        require(!approved[_token], "Token already registered");
        approved[_token] = true;
        emit Registration(_token);
    }
}
