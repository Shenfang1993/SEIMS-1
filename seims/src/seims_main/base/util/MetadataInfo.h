/*!
 * \brief Define MetadataInfo class used by modules
 * \author Junzhi Liu
 * \version 1.0
 * \date June 2010
 */
#pragma once

#include "utilities.h"
#include "text.h"
#include "MetadataInfoConst.h"

using namespace std;

/*!
* \ingroup Util
* \class OutputVariable
* \brief Output variable information class
*/
class VariableMetadata {
public:
	VariableMetadata();
	VariableMetadata(dimensionTypes dimension, string units, string description);
	dimensionTypes Dimension;    ///< Data dimension type	
	string Units;                ///< Units
	string Description;          ///< Description

};

/*!
 * \ingroup util
 * \class ModelClass
 * \brief Module basic description
 */
class ModelClass {
public:
    string Name;
    string Description;
};

/*!
 * \ingroup util
 * \class Parameter
 *
 * \brief Model parameter information class
 */
class Parameter {
public:
	Parameter();
	Parameter(string name, string units, string description, dimensionTypes dimension, string source = Source_ParameterDB);
    string Name;                 ///< Name
    string Units;                ///< Units
    string Description;          ///< Description
    string Source;               ///< Source type
    dimensionTypes Dimension;    ///< Data dimension type
};

/*!
 * \ingroup util
 * \class Information
 *
 * \brief Module development information class
 */
class Information {
public:
    string Id;             ///< Module ID
    string Name;           ///< Module Name
    string Description;    ///< Module Description
    string Version;        ///< Module Version
    string Author;         ///< Author
    string EMail;          ///< Email
    string Website;        ///< Website
    string Helpfile;       ///< Helpfile
};

/*!
 * \ingroup util
 * \class InputVariable
 *
 * \brief Input variable information class
 */
class InputVariable {
public:
	InputVariable();
	InputVariable(string name, string units, string description, dimensionTypes dimension, string source = Source_Module);
    string Name;                ///< Name
    string Units;               ///< Units
    string Description;         ///< Description
    string Source;              ///< Source
    dimensionTypes Dimension;   ///< Data dimension type
};

/*!
 * \ingroup Util
 * \class OutputVariable
 * \brief Output variable information class
 */
class OutputVariable {
public:
	OutputVariable();
	OutputVariable(string name, string units, string description, dimensionTypes dimension);
    string Name;                 ///< Name
    string Units;                ///< Units
    string Description;          ///< Description
    dimensionTypes Dimension;    ///< Data dimension type
};

/*!
 * \ingroup Util
 * \class MetadataInfo
 * \brief Metadata information of module
 */
class MetadataInfo {
private:
    string m_strSchemaVersion;                ///< latest XML schema version supported by this class
    ModelClass m_oClass;                      ///< class name for the module
    Information m_Info;                       ///< the general information for the module
    vector <InputVariable> m_vInputs;         ///< list of input parameters for the module
    vector <OutputVariable> m_vOutputs;       ///<list of output parameters for the module
    vector <ModelClass> m_vDependencies;      ///< list of dependency classes for the module
    vector <Parameter> m_vParameters;         ///< list of parameters for the module

    void OpenTag(string name, string attributes, int indent, string *sb);

    void CloseTag(string name, int indent, string *sb);

    void FullTag(string name, int indent, string content, string *sb);

    void WriteClass(int indent, string *sb);

    void WriteInformation(int indent, string *sb);

    void WriteInputs(int indent, string *sb);

    void WriteOutputs(int indent, string *sb);

    void WriteParameters(int indent, string *sb);

    void WriteDependencies(int indent, string *sb);

    void WriteXMLHeader(string *sb);

    void DimensionTag(string tag, int indent, dimensionTypes dimType, string *sb);

public:
    MetadataInfo(void);

    ~MetadataInfo(void);

    string SchemaVersion(void);

    void SetClass(string name, string description);

    string GetClassName(void);

    string GetClassDescription(void);

    void SetID(string ID);

    string GetID(void);

    void SetName(string name);

    string GetName(void);

    void SetDescription(string description);

    string GetDescription(void);

    void SetVersion(string version);

    string GetVersion(void);

    void SetAuthor(string author);

    string GetAuthor(void);

    void SetEmail(string email);

    string GetEmail(void);

    void SetWebsite(string site);

    string GetWebsite(void);

    void SetHelpfile(string file);

    string GetHelpfile(void);

    int GetInputCount(void);

    int AddInput(string name, string units, string desc, string source, dimensionTypes dimType);

    string GetInputName(int index);

    string GetInputUnits(int index);

    string GetInputDescription(int index);

    string GetInputSource(int index);

    dimensionTypes GetInputDimension(int index);

    InputVariable GetInput(int index);

    int GetOutputCount(void);

    int AddOutput(string name, string units, string desc, dimensionTypes dimType);

    string GetOutputName(int index);

    string GetOutputUnits(int index);

    string GetOutputDescription(int index);

    dimensionTypes GetOutputDimension(int index);

    OutputVariable GetOutput(int index);

    int GetParameterCount(void);

    int AddParameter(string name, string units, string desc, string source, dimensionTypes dimType);

    string GetParameterName(int index);

    string GetParameterUnits(int index);

    string GetParameterDescription(int index);

    string GetParameterSource(int index);

    dimensionTypes GetParameterDimension(int index);

    Parameter GetParameter(int index);

    int GetDependencyCount(void);

    int AddDependency(string name, string description);

    string GetDependencyName(int index);

    string GetDependencyDescription(int index);

    ModelClass GetDependency(int index);

    string GetXMLDocument(void);

	/*!
	* \brief Add metadata about parameters, inputs and outputs of a SimulationModule to a XML class
	*/
	template<typename T>
	static void AddModuleMetadata(MetadataInfo& mdi){
		for (map<const string, VariableMetadata>::iterator iter = T::parameterInfo.begin(); iter != T::parameterInfo.end(); iter++){
			mdi.AddParameter(iter->first, iter->second.Units, iter->second.Description, Source_ParameterDB, iter->second.Dimension);
		}

		for (map<const string, VariableMetadata>::iterator iter = T::inputsInfo.begin(); iter != T::inputsInfo.end(); iter++){
			mdi.AddInput(iter->first, iter->second.Units, iter->second.Description, Source_Module, iter->second.Dimension);
		}

		for (map<const string, VariableMetadata>::iterator iter = T::outputsInfo.begin(); iter != T::outputsInfo.end(); iter++){
			mdi.AddOutput(iter->first, iter->second.Units, iter->second.Description, iter->second.Dimension);
		}
	};

};


