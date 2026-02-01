@integration
Feature: USDm Minting
  As a user of the USDm minting client
  I want to mint USDm tokens
  So that I can participate in the MegaETH ecosystem

  Background:
    Given valid configuration is loaded

  @happy-path
  Scenario: Build a mint order from RFQ response
    Given an RFQ response for minting 1000 USDm
    When I build an order from the RFQ response
    Then the order should have order_type "MINT"
    And the order should have the correct collateral amount
    And the order should have a valid expiry timestamp

  @happy-path
  Scenario: Sign a mint order with EIP-712
    Given an RFQ response for minting 1000 USDm
    And I build an order from the RFQ response
    When I sign the order with my private key
    Then the signature should be valid
    And the signer address should match my wallet

  @happy-path
  Scenario: Dry run mint operation
    Given an RFQ response for minting 1000 USDm
    When I perform a dry run of the mint operation
    Then I should receive a complete dry run result
    And the result should include the RFQ data
    And the result should include the signed order
    And the result should include the EIP-712 domain

  @validation
  Scenario: Mint order uses benefactor as default beneficiary
    Given an RFQ response for minting 1000 USDm
    When I build an order without specifying a beneficiary
    Then the beneficiary should equal the benefactor

  @validation
  Scenario: Mint order accepts custom beneficiary
    Given an RFQ response for minting 1000 USDm
    When I build an order with a custom beneficiary "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    Then the beneficiary should be "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
