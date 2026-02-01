@integration
Feature: Token Allowances
  As a user of the USDm minting client
  I want to manage token allowances
  So that I can authorize the minting contract to spend my tokens

  Background:
    Given valid configuration is loaded

  @validation
  Scenario: Detect insufficient allowance
    Given an RFQ response for minting 1000 USDm
    And the current allowance is 0
    When I check if allowance is sufficient for the order
    Then the allowance should be insufficient

  @validation
  Scenario: Detect sufficient allowance
    Given an RFQ response for minting 1000 USDm
    And the current allowance is 2000000000
    When I check if allowance is sufficient for the order
    Then the allowance should be sufficient
