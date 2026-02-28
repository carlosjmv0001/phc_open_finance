Feature: Personhood Credentials in Open Finance  
  As an AI Agent (Bot)  
  I want to prove that I represent a valid human  
  To access sensitive banking data  
  
  Background:  
    Given the agents are running  
    And the connections are established  
  
  @e2e  
  Scenario: Full issuance and verification flow  
    When the Government issues a personhood credential  
    Then the Bot stores the credential  
    When the Bank requests proof of personhood  
    Then the Bot presents a valid proof  
    And the Bank grants access  
  
  @e2e @revocation  
  Scenario: Revocation blocks future access  
    Given the Bot has a valid credential  
    When the Government revokes the credential  
    And the Bank requests a new proof  
    Then the Bot cannot present a valid proof  
    And the Bank denies access  
  
  @e2e @error  
  Scenario: Failure when DID is not registered  
    Given the Government has no public DID  
    When it tries to issue a credential  
    Then the process fails with an appropriate error  
  
  @e2e @error  
  Scenario: Failure when Tails Server is unavailable  
    Given the Tails Server is offline  
    When trying to create a revocable credential  
    Then the process fails or continues without revocation