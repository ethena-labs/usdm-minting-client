@integration
Feature: USDm Redeeming
  As a user of the USDm minting client
  I want to redeem USDm tokens for collateral
  So that I can exit my USDm position

  Background:
    Given valid configuration is loaded

  @happy-path
  Scenario: Build a redeem order from RFQ response
    Given an RFQ response for redeeming 500 USDm
    When I build an order from the RFQ response
    Then the order should have order_type "REDEEM"
    And the order should have the correct USDm amount
    And the order should have a valid expiry timestamp

  @happy-path
  Scenario: Sign a redeem order with EIP-712
    Given an RFQ response for redeeming 500 USDm
    And I build an order from the RFQ response
    When I sign the order with my private key
    Then the signature should be valid
    And the signer address should match my wallet

  @validation
  Scenario: Different order types produce different signatures
    Given an RFQ response for minting 1000 USDm
    And I build and sign the order as "mint_signed"
    And an RFQ response for redeeming 1000 USDm
    And I build and sign the order as "redeem_signed"
    Then the signatures should be different
