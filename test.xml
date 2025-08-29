<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/DMN/20180521/MODEL/"
             xmlns:dmndi="http://www.omg.org/spec/DMN/20180521/DMNDI/"
             xmlns:dc="http://www.omg.org/spec/DMN/20180521/DC/"
             xmlns:di="http://www.omg.org/spec/DMN/20180521/DI/"
             id="M03001"
             name="M03001"
             typeLanguage="http://www.omg.org/spec/DMN/20180521/FEEL/"
             expressionLanguage="http://www.omg.org/spec/DMN/20180521/FEEL/"
             namespace="http://www.trisotech.com/dmn/definitions/_16d3e5a8-5c91-4a5c-9d7a-4b9a7b5e5d6b">

  <itemDefinition id="tRiskLevel" structureRef="string"/>
  <itemDefinition id="tRiskScore" structureRef="string"/>

  <inputData id="RiskLevel" name="Risk Level">
    <variable id="RiskLevel" name="Risk Level" typeRef="tRiskLevel"/>
  </inputData>

  <decision id="RiskScore" name="Risk Score">
    <variable id="RiskScore" name="Risk Score" typeRef="tRiskScore"/>
    <informationRequirement ref="RiskLevel"/>
    <decisionTable id="RiskScoreDecisionTable" hitPolicy="First">
      <input id="InputRiskLevel" label="Risk Level" typeRef="tRiskLevel"/>
      <output id="OutputRiskScore" label="Risk Score" typeRef="tRiskScore"/>
      <rule>
        <inputEntry>Low</inputEntry>
        <outputEntry>Low</outputEntry>
      </rule>
      <rule>
        <inputEntry>Medium</inputEntry>
        <outputEntry>Medium</outputEntry>
      </rule>
      <rule>
        <inputEntry>High</inputEntry>
        <outputEntry>High</outputEntry>
      </rule>
    </decisionTable>
  </decision>

  <dmndi:DMNDI>
    <dmndi:DMNDiagram>
      <dmndi:DMNDiagramElement dmnElementRef="RiskLevel">
        <di:Bounds x="100" y="100" width="100" height="80"/>
      </dmndi:DMNDiagramElement>
      <dmndi:DMNDiagramElement dmnElementRef="RiskScore">
        <di:Bounds x="300" y="100" width="100" height="80"/>
      </dmndi:DMNDiagramElement>
    </dmndi:DMNDiagram>
  </dmndi:DMNDI>
</definitions>